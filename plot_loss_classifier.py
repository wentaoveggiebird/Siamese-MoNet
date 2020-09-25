import json
import argparse
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

def get_args():
    parser = argparse.ArgumentParser('python')

    parser.add_argument('-run',
                        required=True,
                        type=int,
                        help='which experiment.')

    return parser.parse_args()

def plot_loss(train_loss, train_acc, val_loss, val_acc, loss_dir, time):
    """
    Plot loss.
    """
    font = {'size'   : 14}
    matplotlib.rc('font', **font)   

    epochs = np.array(range(time), dtype=int) + 1
    fig = plt.figure(figsize=(10, 8))
    plt.title('loss & acc')
    plt.xlabel('epoch')
    plt.ylabel('loss & acc')    
    plt.grid(True)

    # find minimum validaiton loss
    min_val_loss = np.min(val_loss)
    pos = np.nonzero(val_loss == min_val_loss)[0]
    max_val_acc = val_acc[pos[0]]
    plt.axvline(x=pos, linewidth=2, color='grey', linestyle='--')
    plt.text(pos+0.5, max_val_acc+0.05, 'val acc: ' + str(max_val_acc)[0:6])

    # plot train and validation curve
    train_loss = np.array(train_loss)
    train_acc = np.array(train_acc)
    val_loss = np.array(val_loss)
    val_acc = np.array(val_acc)
    plt.plot(train_loss, label='Train loss', linewidth=2)
    plt.plot(train_acc, label='Train acc', linewidth=2)
    plt.plot(val_loss, label='Val loss', linewidth=2)
    plt.plot(val_acc, label='Val acc', linewidth=2)
    plt.legend()
    
    plt.savefig(loss_dir)

if __name__=="__main__":
    args = get_args()
    run = args.run

    loss_dir = './results/classifier_run_{}/train_classifier_results_{}.json'.format(run, run)
    with open(loss_dir, "r") as read_file:
        data = json.load(read_file)

    train_loss = data['train_losses']
    train_acc = data['train_accs']
    val_loss = data['val_losses']
    val_acc = data['val_accs']
    time = len(train_loss)
    plot_loss(train_loss=train_loss, train_acc=train_acc, val_loss=val_loss, val_acc=val_acc, 
                loss_dir='./results/classifier_run_{}/loss_{}.png'.format(run, run), time=time)

    