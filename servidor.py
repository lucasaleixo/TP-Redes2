# ========================================================================
 # Projeto destinado a disciplina de Redes de Computadores II
 # Autores: Lucas Aleixo de Paula e Lucas Olini
 # Entrega: 08/06/2018
 # ======================================================================== 

import socket
from socket import timeout
import struct
import sys
import os
import pickle
import time

ADDRESS = '224.1.1.1'
PORTA_MULTICAST = 3333
PORTA_RESPOSTA = 4321

class Mensagem(object):
    tipo = None # 1 - Pegar id inicial; 2 - Resposta id inicial; 3 - Pedido Heartbeat; 4 - Resposta Hearbeat ; 5 - Calculo;  6 - Reposta Calculo
    id_servidor = None
    numero_1 = None
    numero_2 = None
    operacao = ""
    resultado = ""

    def __init__(self, tipo, id_servidor=None, numero_1=None, numero_2=None, operacao=None, resultado=None):
        self.tipo = tipo
        self.id_servidor = id_servidor
        self.numero_1 = numero_1
        self.numero_2 = numero_2
        self.operacao = operacao
        self.resultado = resultado

class Servidor(object):
    servidor_id = None
    lista_servidores = []

    def __init__(self, lista_servidores=[], servidor_id=None):
        self.servidor_id = servidor_id
        self.lista_servidores = lista_servidores
        # Define o socket de recebimento, e conecta de acordo com a porta passada como parametro
        self.socket_recebimento = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket_recebimento.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_recebimento.bind(('', PORTA_MULTICAST))
        # Define o grupo MULTICAST, e adiciona o servidor ao grupo de MULTICAST
        mreq = struct.pack('4sl', socket.inet_aton(ADDRESS), socket.INADDR_ANY)
        self.socket_recebimento.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        # Define o socket de envio
        self.socket_envio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket_envio.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)

# Funcao principal do servidor
def mcast_server(log):
    servidor = Servidor([], None)
    mensagem = Mensagem(1, None, None, None, None)
    mensagem_serializada = pickle.dumps(mensagem, 2)
    maior_id = 0
    servidor.socket_recebimento.settimeout(3)
    servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
    while True:
        try:
            data, addr = servidor.socket_recebimento.recvfrom(1024)
            mensagem = pickle.loads(data)
            print(str(mensagem.tipo) + " " + str(mensagem.id_servidor))
            if mensagem.tipo == 2:
                if mensagem.id_servidor != None:
                    if maior_id < mensagem.id_servidor:
                        maior_id = mensagem.id_servidor
                    servidor.lista_servidores.append((mensagem.id_servidor, time.time()))
        except timeout:
            break
    servidor.socket_recebimento.settimeout(None)
    print(servidor.lista_servidores)
    if (maior_id != 0):
        # Atribuindo id do servidor
        print >>sys.stderr, '\nAtribuindo id = %s ao servidor' % str(maior_id + 1)
        log.write("\nServidores descobertos e salvos na lista de servidores\n")
        servidor.servidor_id = maior_id + 1
    elif (maior_id == 0):
        # Ainda nao tem nenhum servidor, este vai ser o servidor 1
        print >>sys.stderr, '\nNenhum servidor encontrado, atribuindo id 1 ao servidor'
        log.write("\nNenhum servidor encontrado, atribuindo id 1 ao servidor\n")
        servidor.servidor_id = 1
    log.write("\n################################################")

    # Loop de requisicoes e respostas
    while True:
        # Escuta no endereco e porta passados como parametro
        print >>sys.stderr, '\nAguardando receber mensagem'
        log.write("\nAguardando receber mensagem")
        servidor.socket_recebimento.settimeout(1)
        hearbeat_timer = time.time() + 5
        while hearbeat_timer > time.time():
            try:
                data, addr = servidor.socket_recebimento.recvfrom(1024)
                mensagem = pickle.loads(data)
                # Novo servidor entrando na rede
                if (mensagem.tipo == 1):
                    print >>sys.stderr, "\nNovo servidor entrando na rede, enviando o id deste servidor"
                    log.write("\nNovo servidor entrando na rede, enviando o id deste servidor")
                    mensagem = Mensagem(2, servidor.servidor_id, None, None, None, None)
                    mensagem_serializada = pickle.dumps(mensagem, 2)
                    servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
                # Pedido de heartbeat
                elif (mensagem.tipo == 3):   
                    print >>sys.stderr, '\nchegou pedido de id, este servidor id = %s' % servidor.servidor_id   
                    mensagem = Mensagem(4, servidor.servidor_id, None, None, None, None)     
                    mensagem_serializada = pickle.dumps(mensagem, 2)
                    servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
                # Calculo
                elif (mensagem.tipo == 5):
                    servidor_lider = True
                    for serv in servidor.lista_servidores:
                        if serv[0] < servidor.servidor_id:
                            servidor_lider = False
                    if servidor_lider:
                        print >>sys.stderr, 'sending acknowledgement to', ADDRESS
                        log.write("\nsending acknowledgement to %s\n" % str(ADDRESS))
                        mensagem = Mensagem(6, servidor.servidor_id, None, None, None, eval(mensagem.operacao))
                        mensagem_serializada = pickle.dumps(mensagem, 2)
                        servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_RESPOSTA))
            except timeout:
                print >>sys.stderr, '\nNenhuma mensagem recebida em 1 segundo, checando se ja passou o tempo para a atualizacao da lista de servidores'
                log.write("\nNenhuma mensagem recebida em 1 segundo, checando se ja passou o tempo para a atualizacao da lista de servidores")
        servidor.socket_recebimento.settimeout(None)

        # Atualiza a lista de servidores
        print >>sys.stderr, '\n5 segundos se passaram, iniciando processo para atualizar a lista de servidores ativos'
        log.write("\n5 segundos se passaram, iniciando processo para atualizar a lista de servidores ativos")
        servidor.lista_servidores = []
        mensagem = Mensagem(3, None, None, None, None, None)
        mensagem_serializada = pickle.dumps(mensagem, 2)
        servidor.socket_recebimento.settimeout(2)
        servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
        while True:
            try:
                print("antes do recebimento")
                data, addr = servidor.socket_recebimento.recvfrom(1024)
                mensagem = pickle.loads(data)
                print(str(mensagem.tipo) + str(mensagem.id_servidor))
                if (mensagem.tipo == 4):
                    if (mensagem.id_servidor != None):
                        servidor.lista_servidores.append((mensagem.id_servidor, time.time()))
            except timeout:
                break
        print servidor.lista_servidores
        servidor.socket_recebimento.settimeout(None)
        log.write("\n################################################\n")  

# Funcao main
if __name__ == '__main__':

    # Abre o arquivo log_servidor em modo de escrita
    log = open("log_servidor.txt","a")
    addr = ""
    port = 0
    # Opcao para receber o endereco e porta como parametro
    try:
        addr = sys.argv[1]
        port = int(sys.argv[2])

    # Se os parametros estiverem incompletos, emite mensagem de erro
    except IndexError:
        print 'use: %s addr port' % sys.argv[0]
        sys.exit(1)

    log.write("# ==========================================================")
    log.write("\n# Projeto destinado a disciplina de Redes de Computadores II")
    log.write("\n# Autores: Lucas Aleixo de Paula e Lucas Olini")
    log.write("\n# Entrega: 08/06/2018")
    log.write("\n# ==========================================================\n")
    log.write("########################\n")        

    # Apos o cabecalho, os dados dos demais servidores sao inseridos no log
    log.write("Endereco: %s\nPorta: %d\n" % (addr,port))
    log.write("Process ID: %d\n" % 1)
    log.write("########################\n")        
    log.close()

    print 'running server on %s:%d' % (addr, port)
    print 'Process ID: ', '1'

    # Passa o log e a tabela como parametro para a funcao do servidor
    log = open("log_servidor.txt","a")
    mcast_server(log)
    log.close()
