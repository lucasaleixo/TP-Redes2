# ========================================================================
 # Projeto destinado a disciplina de Redes de Computadores II
 # Autores: Lucas Aleixo de Paula e Lucas Olini
 # Entrega: 08/06/2018
 # ======================================================================== 

import socket
import struct
import sys
import os
import pickle
import time

class Mensagem(object):
    tipo = None # 1 - Heartbeat ; 2 - Calculo;
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

# Funcao principal do servidor
def mcast_server(addr, port, pid, log, tabela):
    # Define o socket, e conecta de acordo com a porta passada como parametro
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))

    # Define o grupo MULTICAST, e adiciona o servidor ao grupo de MULTICAST
    mreq = struct.pack('4sl', socket.inet_aton(addr), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    servidor = Servidor([], None)
    mensagem = Mensagem(1, None, None, None, None)
    mensagem_serializada = pickle.dumps(mensagem, 2)
    sent = sock.sendto(mensagem_serializada, (addr, port))
    sock.settimeout(4)
    maior_id = 0
    t_end = time.time() + 3
    while time.time() < t_end:
        try:
            data, addr = sock.recvfrom(1024)
            mensagem = pickle.loads(data)
            if maior_id < mensagem.id_servidor:
                maior_id = mensagem.id_servidor
            servidor.lista_servidores.append((mensagem.id_servidor, time.time()))
        except:
            # Ainda nao tem nenhum servidor, este vai ser o servidor 1
            print >>sys.stderr, '\nNenhum servidor encontrado, atribuindo id 1 ao servidor'
            log.write("\nNenhum servidor encontrado, atribuindo id 1 ao servidor\n")
            servidor.servidor_id = 1
    if maior_id != 0:
        # Atribuindo id do servidor
        print >>sys.stderr, '\nAtribuindo id = %s ao servidor' % maior_id + 1
        servidor.servidor_id = maior_id + 1
        print >>sys.stderr, '\nAtribuindo id = %s ao servidor' % servidor.servidor_id
    log.write("\n################################################")        
    sock.settimeout(None)
    try:
        # Loop de requisicoes e respostas
        while True:
            # Escuta no endereco e porta passados como parametro
            print >>sys.stderr, '\nwaiting to receive message'
            log.write("\nwaiting to receive message\n")
            data, addr = sock.recvfrom(1024)
            mensagem = pickle.loads(data)

            # Ao receber uma nova mensagem, registra no log de execucao
            print >>sys.stderr, 'received %s bytes from %s' % (len(data), addr)
            log.write("received %s bytes from %s\n" % (len(data), addr))
            print >>sys.stderr, data
            log.write(data)	  

            # Se o servidor tiver o MENOR process_id, responde para o cliente
            if(int(tabela[0]) == pid):
                print >>sys.stderr, 'sending acknowledgement to', addr

            # Regristra a resposta no log de execucao dos servidores
            log.write("\nsending acknowledgement to %s\n" % str(addr))
            mensagem.resultado =  eval(str(mensagem.numero_1) + mensagem.operacao + str(mensagem.numero_2))
            mensagem_serializada = pickle.dumps(mensagem, 2)
            sock.sendto(mensagem_serializada, addr)

        log.write("\n################################################\n")  

    # Ao encerrar a execucao, fecha o servidor
    except KeyboardInterrupt:
        print 'done'
        sys.exit(0)

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

    # Com o endereco definido, registra o PROCESS_ID da instancia
    pid = os.getpid()

    # Arquivo temporario, usado para armazenar os PROCESS_ID
    f = open("servidores.txt","a")
    f.write("%d\n" % pid)
    f.close()

    # Le os dados do arquivo, e armazena em uma tabela
    with open("servidores.txt", "r") as servidores:
        tabela = []
        for line in servidores:
            tabela.append(line)

    # Se o PROCESS_ID da instancia for o menor, insere o cabecalho no log
    if(int(tabela[0]) == pid):
        log.write("# ==========================================================")
        log.write("\n# Projeto destinado a disciplina de Redes de Computadores II")
        log.write("\n# Autores: Lucas Aleixo de Paula e Lucas Olini")
        log.write("\n# Entrega: 08/06/2018")
        log.write("\n# ==========================================================\n")
        log.write("########################\n")        

    # Apos o cabecalho, os dados dos demais servidores sao inseridos no log
    log.write("Endereco: %s\nPorta: %d\n" % (addr,port))
    log.write("Process ID: %d\n" % pid)
    log.write("########################\n")        
    log.close()

    print 'running server on %s:%d' % (addr, port)
    print 'Process ID: ', pid

    # Passa o log e a tabela como parametro para a funcao do servidor
    log = open("log_servidor.txt","a")
    mcast_server(addr, port, pid, log, tabela)
    log.close()
