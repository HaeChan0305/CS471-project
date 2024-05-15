import torch
from torch_geometric.nn import GCNConv
#from torch_geometric.nn import GraphConv, TopKPooling
from torch_geometric.nn import global_mean_pool as gap, global_max_pool as gmp
import torch.nn.functional as F
from layers import SAGPool#, DualGCNConv
from cycle import CycleProcessor




class Net(torch.nn.Module):
    def __init__(self,args):
        super(Net, self).__init__()
        self.args = args
        self.num_features = args.num_features
        self.nhid = args.nhid
        self.num_classes = args.num_classes
        self.pooling_ratio = args.pooling_ratio
        self.dropout_ratio = args.dropout_ratio
        self.cycle_processor = CycleProcessor()
        
        print(self.num_features, self.nhid)

        self.conv1 = GCNConv(self.num_features, self.nhid)

        self.pool1 = SAGPool(self.nhid, ratio=self.pooling_ratio)
        self.conv2 = GCNConv(self.nhid, self.nhid)
        self.pool2 = SAGPool(self.nhid, ratio=self.pooling_ratio)
        self.conv3 = GCNConv(self.nhid, self.nhid)
        self.pool3 = SAGPool(self.nhid, ratio=self.pooling_ratio)

        self.lin1 = torch.nn.Linear(self.nhid*2, self.nhid)
        self.lin2 = torch.nn.Linear(self.nhid, self.nhid//2)
        self.lin3 = torch.nn.Linear(self.nhid//2, self. num_classes)

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        print("only node")
        print(x.shape, edge_index.shape, batch.shape)
        print()
        
        x, edge_index, batch = self.cycle_processor(data.x, data.edge_index, data.batch)
        print("node + cycle")
        print(x.shape, edge_index.shape, batch.shape)
        print()
        
        # x_node, edge_index_node, batch_node = NotImplemented
        # x_cycle, edge_index_cycle, batch_cycle = NotImplemented
        
        # x = torch.cat([x_node, x_cycle], dim=0)
        # edge_index = torch.cat([edge_index_node, edge_index_cycle], dim=1)
        # batch = torch.cat([batch_node, batch_cycle], dim=0)
        
        x = F.relu(self.conv1(x, edge_index))
        print("after conv")
        print(x.shape)
        print()
        
        x, edge_index, _, batch, perm = self.pool1(x, edge_index, None, batch)        
        print("after pooling")
        
        print("x")
        print(x.shape)
        print(x)
        print()
        
        print("edge_index")
        print(edge_index.shape)
        print(edge_index)
        print()
        
        print("batch")
        print(batch.shape)
        print(batch)
        print()
        
        print("perm")
        print(perm.shape)
        print(perm)
        print()
        
        print(perm[batch == 0])
        
        x1 = torch.cat([gmp(x, batch), gap(x, batch)], dim=1)
        print(x1.shape)
        print()

        print(max(edge_index[0]), max(edge_index[1]))
        print()
        
        assert 0
        
        x = F.relu(self.conv2(x, edge_index))
        x, edge_index, _, batch, _ = self.pool2(x, edge_index, None, batch)
        x2 = torch.cat([gmp(x, batch), gap(x, batch)], dim=1)

        x = F.relu(self.conv3(x, edge_index))
        x, edge_index, _, batch, _ = self.pool3(x, edge_index, None, batch)
        x3 = torch.cat([gmp(x, batch), gap(x, batch)], dim=1)

        x = x1 + x2 + x3

        x = F.relu(self.lin1(x))
        x = F.dropout(x, p=self.dropout_ratio, training=self.training)
        x = F.relu(self.lin2(x))
        x = F.log_softmax(self.lin3(x), dim=-1)

        return x

    