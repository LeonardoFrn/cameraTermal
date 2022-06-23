#! /usr/bin/python3
# adicionando as bibliotecas para o funcionamento do prototipo
import time,board,busio
import numpy as np
import adafruit_mlx90640
import matplotlib.pyplot as plt
from scipy import ndimage
import argparse
import requests

dadosCamera = argparse.ArgumentParser(description='Thermal Camera Program')
dadosCamera.add_argument('--mirror', dest='imageMirror', action='store_const', default='false',
                    const='imageMirror', help='Flip the image for selfie (default: false)')
arrayCamera = dadosCamera.parse_args()
imageMirror = arrayCamera.imageMirror

if(imageMirror == 'false'):
    print('Mirror mode: false')
else:
    imageMirror = 'true'
    print('Mirror mode: true')

i2c = busio.I2C(board.SCL, board.SDA, frequency=400000) # setup I2C
mlx = adafruit_mlx90640.MLX90640(i2c) # inicio da comunicacao com a camera MLX90640
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_8_HZ #taxa de atualizacao
mlx_shape = (24,32) # forma da camera mlx90640

interpolacao = 10 # interpolacao
interpolacaoForma = (mlx_shape[0]*interpolacao,
                    mlx_shape[1]*interpolacao) # nova forma

figura = plt.figure(figsize=(12,9)) # inicio da reproducao
planoFundo = figura.add_subplot(111) # adiciona subplot
figura.subplots_adjust(0.05,0.05,0.95,0.95) # libera subplot desnecessario
termico = planoFundo.imshow(np.zeros(interpolacaoForma),interpolation='none',
                   cmap=plt.cm.bwr,vmin=25,vmax=45) # imagem inicial
cbar = figura.colorbar(termico) # configuracao barra de cores
cbar.set_label('Temperature [$^{\circ}$C]',fontsize=14) # barra de cores

figura.canvas.draw() # plano de fundo
copiaPlanoFundo = figura.canvas.copy_from_bbox(planoFundo.bbox) # copia do plano de fundo
planoFundo.text(-75, 125, 'Max:', color='red')
valorMaximo = planoFundo.text(-75, 150, 'test1', color='black')
figura.show() # exibicao da imagem da camera

frame = np.zeros(mlx_shape[0]*mlx_shape[1]) # 768 pts
def plot_update():
    figura.canvas.restore_region(copiaPlanoFundo) # restaurar o plano de fundo
    mlx.getFrame(frame) # leitura da camera mlx90640
    data_array = np.fliplr(np.reshape(frame,mlx_shape)) # remodelar os dados
    if(imageMirror == 'true'):
        data_array = np.flipud(data_array)
    data_array = ndimage.zoom(data_array,interpolacao) # adicionando dados da imagem no array
    termico.set_array(data_array) # adicionando o array de dados
    termico.set_clim(vmin=np.min(data_array),vmax=np.max(data_array)) # definindo os limites da camera
    cbar.on_mappable_changed(termico) # atualizar o intervalo da barra de cores
    plt.pause(0.001)
    planoFundo.draw_artist(termico) # desenhar nova imagem térmica
    valorMaximo.set_text(str(np.round(np.max(data_array), 1)))
    figura.canvas.blit(planoFundo.bbox) # desenhando a imagem do plano de fundo
    figura.canvas.flush_events() # exibicao da imagem da camera
    figura.show()
    return

t_array = []
while True:
    t1 = time.monotonic() # determinando a taxa de quadros
    try:
        plot_update() # atualizacao da exibicao
    except:
        continue
    # taxa de quadros aproximado
    t_array.append(time.monotonic()-t1)
    if len(t_array)>10:
        t_array = t_array[1:] # taxa de quadros aproximado
    print('Frame Rate: {0:2.1f}fps'.format(len(t_array)/np.sum(t_array)))

    print('Average MLX90640 Temperature: {0:2.1f}C ({1:2.1f}F)'.\
      format(np.mean(frame),(((9.0/5.0)*np.mean(frame))+32.0)))
    temp = 'Average MLX90640 Temperature: {0:2.1f}C ({1:2.1f}F)'.\
      format(np.mean(frame),(((9.0/5.0)*np.mean(frame))+32.0))
    response = requests.get("https://be-t024-tcc.herokuapp.com/api/temperatura/add/"+temp)
    print(response)
