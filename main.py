from pandas_ods_reader import read_ods
import os
import requests
import json

folder = './tables'
colors = ["INCOLOR","VERDE","FUME"]

def read_files(fileName):
    data = read_ods('tables/' + fileName, columns=["A"])
    dict = data.to_dict()
    keys = dict.keys()
    count = 0
    for key in keys:
        values = dict.get(key)
        for x in values:
            for color in colors:
                count = count+1
                sheets = fileName.replace("janela_","").replace(".ods","").replace("box_","").replace("porta_","").replace("open","").upper()

                if not sheets:
                    sheets = "1F"

                sheets = sheets.replace("_","")
                width = values[x][0:3].replace("x","")
                height = values[x][4:7]
                type = fileName.replace("_4f.ods","").replace("_2f.ods","").replace(".ods","").replace("_open","").upper()

                if sheets == "BASCULA":
                    type = "JANELA"
                    sheets = "1F"
                    height = width

                if type == "PORTA" or type == "JANELA":
                    aux = width
                    width = height
                    height = aux

                largura = width
                altura = height
                category = "VIDRO-TEMPERADO"
                product = {
                    "category": category,
                    "type": type,
                    "sheets": sheets,
                    "width": largura,
                    "height": altura,
                    "color": color,
                    "key": category+'-'+type+'-'+sheets+'-'+color+'-'+width+'-'+height
                }
                headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
                reponse = requests.post('http://localhost:8000/verly-service/product', data=json.dumps(product), headers=headers)
                print(product)
                print("------------------------------")
                print(reponse.status_code)

if __name__ == '__main__':

    files = []
    for diretorio, subpastas, arquivos in os.walk(folder):
        for arquivo in arquivos:
            files.append(os.path.join(arquivo))



    for file in files:
        read_files(file)