"""
Generate embeddings and visualize them in 2-d plane
"""
import random
import argparse
import os
import torch
import numpy as np
from dataloader import read_cluster_file, select_classes, divide_clusters, pocket_loader_gen
from compute_acc import compute_embeddings
from model import SiameseNet
from sklearn.manifold import TSNE

import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt

def get_args():
    parser = argparse.ArgumentParser('python')

    parser.add_argument('-embed',
                        default=True,
                        required=False,
                        help='whether to generate embeddings.')

    parser.add_argument('-embedding_dir',
                        default='../embeddings/',
                        required=False,
                        help='text file to get the cluster labels')                        

    parser.add_argument('-cluster_file_dir',
                        default='../data/googlenet-classes',
                        required=False,
                        help='text file to get the cluster labels')

    parser.add_argument('-pocket_dir',
                        default='../data/googlenet-dataset/',
                        required=False,
                        help='directory of pockets')

    parser.add_argument('-pop_dir',
                        default='../data/pops-googlenet/',
                        required=False,
                        help='directory of popsa files for sasa feature')

    parser.add_argument('-trained_model_dir',
                        default='../trained_models/trained_model_7.pt',
                        required=False,
                        help='directory to store the trained model.')                        

    return parser.parse_args()


def gen_embedding(cluster_file_dir, pocket_dir, pop_dir, trained_model_dir):
    """Generate embeddings of the given dataloader."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') # detect cpu or gpu
    print('device: ', device)

    batch_size = 4
    print('batch size:', batch_size)
    
    num_workers = os.cpu_count()
    num_workers = int(min(batch_size, num_workers))
    print('number of workers to load data: ', num_workers)

    num_classes = 60
    print('number of classes:', num_classes)
    cluster_th = 10000 # threshold of number of pockets in a class

    normalize = True
    
    # read the original clustered pockets
    clusters = read_cluster_file(cluster_file_dir)

    # select clusters according to rank of sizes and sample large clusters
    clusters = select_classes(clusters, num_classes, cluster_th)

    # divide the clusters into train, validation and test
    train_clusters, val_clusters, test_clusters = divide_clusters(clusters)
    num_train_pockets = sum([len(x) for x in train_clusters])
    num_val_pockets = sum([len(x) for x in val_clusters])
    num_test_pockets = sum([len(x) for x in test_clusters])
    print('number of pockets in training set: ', num_train_pockets)
    print('number of pockets in validation set: ', num_val_pockets)
    print('number of pockets in test set: ', num_test_pockets)

    # missing popsa files for sasa feature at this moment
    features_to_use = ['charge', 'hydrophobicity', 'binding_probability', 'distance_to_center', 'sequence_entropy'] 
    
    # load trained model
    model = SiameseNet(num_features=len(features_to_use), dim=32, train_eps=True, num_edge_attr=1).to(device)
    model.load_state_dict(torch.load(trained_model_dir))
    model.eval()

    # train loader, used to compute the geometric center of the embeddings of each cluster
    dataloader = pocket_loader_gen(pocket_dir=pocket_dir, 
                                     pop_dir=pop_dir,
                                     clusters=test_clusters, 
                                     features_to_use=features_to_use, 
                                     batch_size=batch_size, 
                                     shuffle=False, 
                                     num_workers=num_workers)
        
    embeddings, labels, cluster_set = compute_embeddings(dataloader, model, device, normalize=True)
    return embeddings, labels


def visualize_embeddings(embeddings, labels, cluster_list):
    """Visualize 2d embeddings and color them by labels.
    
       cluster_list: list of cluster numbers we want to visualize
    """
    font = {'size'   : 16}
    matplotlib.rc('font', **font)   
    embedding_list = []
    label_list = []
    for cluster in cluster_list:
        idx = np.nonzero(labels == cluster)[0]
        #print(idx)
        embedding_list.append(embeddings[idx,:])
        label_list.append(labels[idx])
    embedding_list = np.vstack(embedding_list)
    label_list = np.hstack(label_list)
    fig = plt.figure(figsize=(12, 12))
    ax = sns.scatterplot(x=embedding_list[:,0], y=embedding_list[:,1], hue=label_list, markers='.', palette=sns.color_palette("hls", len(list(set(label_list)))))
    plt.savefig('./embedding_visualization/run_7.png')

if __name__=="__main__":
    args = get_args()
    embed = args.embed
    embedding_dir = args.embedding_dir
    cluster_file_dir = args.cluster_file_dir
    pocket_dir = args.pocket_dir
    pop_dir = args.pop_dir
    trained_model_dir = args.trained_model_dir

    name = trained_model_dir.split('/')[-1]
    name = name.split('.')[0]
    embedding_name = name + '_embedding' + '.npy'
    label_name = name + '_label' + '.npy'
    embedding_path = embedding_dir + embedding_name
    label_path = embedding_dir + label_name

    if embed == True:
        embeddings, labels = gen_embedding(cluster_file_dir, pocket_dir, pop_dir, trained_model_dir)
        print('shape of generated embeddings: {}'.format(embeddings.shape))
        print('shape of labels: {}'.format(labels.shape))
        np.save(embedding_path, embeddings)
        np.save(label_path, labels)
    else:
        embeddings = np.load(embedding_path)
        labels = np.load(label_path)
    
        labels = labels.astype(int)
        #tsne_embedding = TSNE(n_components=2).fit_transform(embeddings)
        tsne_embedding_path = embedding_dir + name + '_tsne_embedding' + '.npy'
        #np.save(tsne_embedding_path, tsne_embedding)
        tsne_embedding = np.load(tsne_embedding_path)

        cluster_list = [20, 31 , 33, 36, 39, 45, 46, 54, 58, 59] # 70+
        cluster_list = [3, 12, 19, 21, 47, 52, 53]# 20% plus accuracy
        cluster_list = [2, 4, 15, 34, 44] # 30% plus accuracy
        cluster_list = [6, 18, 20, 29, 32, 38, 43, 55]# 40%+ ~ 60%+
        #cluster_list = [13, 14, 17, 22, 23, 27, 37, 40, 41, 57] # 10% plus accuracy
        #cluster_list = [0, 1, 7, 8, 9, 10, 11, 16, 25, 26, 28] # total failure
        visualize_embeddings(tsne_embedding, labels, cluster_list)
