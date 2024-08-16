from recbole.config import Config
from recbole.data import create_dataset, data_preparation
from logging import getLogger
#from recbole.trainer import Trainer
from models.utils.trainer import Trainer
from recbole.utils import init_seed, init_logger
import torch
import sys
import time 
from recbole.utils import calculate_valid_score
def get_model(model_name):
    return getattr(sys.modules[__name__], model_name)
    
def count_parameters0(model):
        return sum(p.numel() for p in model.parameters() if p.requires_grad)
    
def output_result(config,num_params,exclude_emb_params,test_result,execution_time):
    model_name = str(config['model'])
    data_name = str(config['dataset'])

    output = model_name + "_" + data_name + "_" + str(config['phm']) + "_" + str(config['embedding_size']) + "_" + str(config['hidden_size']) + "_" + str(num_params) + "_" + str(exclude_emb_params) + "_" + str(num_params-exclude_emb_params) + "_" + str(execution_time if test_result != None else 0)
    # 打开文件以追加模式写入
    file_name = model_name + "-" + data_name + ".txt"
    with open(file_name, 'a',encoding='utf-8') as f:
        # 将输出重定向到文件
        print(output, file=f)
        if test_result != None:
            print(test_result,file=f)  
        else:
            print('None',file=f)

def count_parameters(model):
    emb_params = 0
    if hasattr(model,'item_embedding'):
        emb_params += sum(p.numel() for p in model.item_embedding.parameters() if p.requires_grad)
    if hasattr(model,'position_embedding'):
        emb_params += sum(p.numel() for p in model.position_embedding.parameters() if p.requires_grad)
    if hasattr(model,'user_embedding'):
        emb_params += sum(p.numel() for p in model.user_embedding.parameters() if p.requires_grad)   

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    return total_params,total_params-emb_params

def get_test_loss(model,test_data):
    test_loss,cnt = 0,0
    for i in test_data:
        loss = model.calculate_loss(i[0].to(config['device']))
        test_loss += loss
        cnt += 1
    test_loss = test_loss.item() / cnt

    return "{:.4f}".format(test_loss)    

if __name__ == '__main__':
    
    
    config = Config(model='GRU4Rec', dataset='ml-1m', config_file_list=['config/ml-1m.yaml'])
    if config['phm'] == 0:
        from recbole.model.sequential_recommender import GRU4Rec,BERT4Rec,SASRec,STAMP
    else:
        from models.PHM_SASRec import SASRec
        from models.PHM_BERT4Rec import BERT4Rec
        from models.GRU4Rec import GRU4Rec
        from models.STAMP import STAMP
    config = Config(model=config['model_name'], dataset=config['data_name'], config_file_list=['config/' + config['data_name'] +'.yaml'])

    # init random seed
    init_seed(config['seed'], config['reproducibility'])

    dataset = create_dataset(config)

    train_data, valid_data, test_data = data_preparation(config, dataset)

    print(config["phm"])

    #get model accoding to name
    model = get_model(config['model_name'])(config, train_data.dataset).to(config['device'])

        #get the number of parameters of the model
    num_params,exclude_emb_params = count_parameters(model)
    print(num_params,exclude_emb_params,num_params-exclude_emb_params)
    exit(0)
    
    # trainer loading and initialization
    trainer = Trainer(config, model)
    
    # model training

    epochs,best_valid_score, best_valid_result = trainer.fit(train_data, valid_data,show_progress=config["show_progress"])

    # model evaluation

    test_result = trainer.evaluate(test_data,show_progress=config["show_progress"])

    valid_score = calculate_valid_score(test_result,trainer.valid_metric)

    #test_loss = get_test_loss(model,test_data)
    test_loss ="nan"

    output_result(config,num_params,exclude_emb_params,test_result,str("0") + "_lr:" + str(config["learning_rate"]) + "_" + str("0") + "_" + str(test_loss))
