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

# Endereco e porta para recebimento
ADDRESS = '225.1.1.1'
PORTA_MULTICAST = 3333

# Porta para o envio da resposta
PORTA_RESPOSTA = 4321

# Definicao do objeto Mensagem
class Mensagem(object):
    tipo = None # 1 - Pegar id inicial; 2 - Resposta id inicial; 3 - Mensagem Heartbeat; 5 - Calculo;  6 - Reposta Calculo
    id_servidor = None
    operacao = ""
    resultado = ""

    # Inicializa os atributos da Mensagem
    def __init__(self, tipo, id_servidor=None, operacao=None, resultado=None):
        self.tipo = tipo
        self.id_servidor = id_servidor
        self.operacao = operacao
        self.resultado = resultado

# Definicao do objeto Servidor
class Servidor(object):
    servidor_id = None
    lista_servidores = []
  
    # Inicializa os atributos do Servidor
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
def Servidor_Multicast(log):
    # Inicia a lista de servidores vazia
    servidor = Servidor([], None)
    print("Inicializando servidor sem Id e com lista de servidores vazia\n")
    log.write("Inicializando servidor sem Id e com lista de servidores vazia\n")

    # Mensagem inicial do tipo 1, para definir os IDs
    mensagem = Mensagem(1, None, None, None)
    mensagem_serializada = pickle.dumps(mensagem, 2)
    maior_id = 0

    # Define o timeout para o socket e transmite na PORTA_MULTICAST
    servidor.socket_recebimento.settimeout(2)
    servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))

    time_end = time.time() + 5
    # Loop para compor a lista de servidores
    while time_end > time.time():
        try:
	        # Recebe os dados atraves do socket de recebimento
            data, addr = servidor.socket_recebimento.recvfrom(1024)
            mensagem = pickle.loads(data)

	        # Se o tipo da mensagem for 2, verifica o ID
            if mensagem.tipo == 2:
                if mensagem.id_servidor != None:
                    if any(mensagem.id_servidor in servidor for servidor in servidor.lista_servidores):
                        pass
                    else:
    		            # Compara o ID do servidor com o maior ID
                        if maior_id < mensagem.id_servidor:
                            maior_id = mensagem.id_servidor

    		            # Adiciona o servidor a lista de servidores
                        servidor.lista_servidores.append([mensagem.id_servidor, time.time()])
		    log.write("\nAdicionou o servidor na lista de servidores\n")

	   # Se houver timeout, envia novamente. Se terminou o tempo de recebimento inicial, sai do loop
        except timeout:
            if time_end > time.time():
                servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
          
    # Define o timeout para o socket de recebimento
    servidor.socket_recebimento.settimeout(None)

    # Printa a lista de servidores
    print(servidor.lista_servidores)

    # Se o maior ID nao for 0, a lista nao esta vazia
    if (maior_id != 0):
        # Atribuindo id do servidor
        print >>sys.stderr, '\nAtribuindo id = %s ao servidor' % str(maior_id + 1)
        log.write("\nServidores armazenados na lista\n")
        servidor.servidor_id = maior_id + 1

    # Se o maior ID for 0, a lista esta vazia
    elif (maior_id == 0):
    	log.write("##########################################################\n")
        # Ainda nao tem nenhum servidor, este vai ser o servidor 1
        print >>sys.stderr, '\nNenhum servidor encontrado, atribuindo id 1 ao servidor'
        log.write("Nenhum servidor encontrado\n")
        log.write("Atribuindo o ID 1 ao servidor\n")
        servidor.servidor_id = 1

    mensagem = Mensagem(3, servidor.servidor_id, None, None)
    mensagem_serializada = pickle.dumps(mensagem, 2)
    log.write("##########################################################\n")

    # Loop de requisicoes e respostas
    while True:
        # Escuta no endereco e porta passados como parametro
        print >>sys.stderr, '\nAguardando para receber'
        log.write("Aguardando para receber")

	# Define o timeout para o socket de recebimento
        servidor.socket_recebimento.settimeout(1)
        hearbeat_timer = time.time() + 3
        while hearbeat_timer > time.time():
            try:
                data, addr = servidor.socket_recebimento.recvfrom(1024)
                mensagem = pickle.loads(data)

                # Novo servidor entrando na rede
                if (mensagem.tipo == 1):
                    mensagem = Mensagem(2, servidor.servidor_id, None, None)
                    mensagem_serializada = pickle.dumps(mensagem, 2)
                    servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
                    print >>sys.stderr, "\nNovo servidor entrando na rede, enviando o id deste servidor"
                    log.write("\nNovo servidor entrando na rede\n")
                    log.write("Enviando o id deste servidor\n")

                # Mensagem de Heartbeat
                elif (mensagem.tipo == 3):
                    if (mensagem.id_servidor != None):
                        if (mensagem.id_servidor != servidor.servidor_id):
                            servidor_novo = True
                            for serv in servidor.lista_servidores:
                                if serv[0] == mensagem.id_servidor:
                                    serv[1] = time.time()
                                    servidor_novo = False
                            if servidor_novo:
                                servidor.lista_servidores.append([mensagem.id_servidor, time.time()])
                    print(servidor.lista_servidores)

                # Calculo
                elif (mensagem.tipo == 5):
                    servidor_lider = True

		            # Identifica o servidor lider para responder
                    for serv in servidor.lista_servidores:
                        if serv[0] < servidor.servidor_id:
                            servidor_lider = False
                            break

		            # Se for o lider, envia o resultado do calculo
                    if servidor_lider:
                        log.write("\n\nServidor lider identificado")
                        try:
                            index = mensagem.operacao.index("/")
                        except ValueError:
                            index = -1
                        if index != -1:
                            if (mensagem.operacao[index+1] == '0'):
                                resultado_calculo = "ERRO: Divisao por zero. Nao eh possivel calcular."
                            else:
                                resultado_calculo = eval(mensagem.operacao)
                        else:
                            resultado_calculo = eval(mensagem.operacao)
                        print >>sys.stderr, '\nEnviando resultado do calculo para o cliente.\nResultado = %s \n' % resultado_calculo
                        log.write("\nEnviando resultado do calculo para o cliente.\nResultado = %s \n" % resultado_calculo)
                        mensagem = Mensagem(6, servidor.servidor_id, None, resultado_calculo)
                        mensagem_serializada = pickle.dumps(mensagem, 2)
                        servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_RESPOSTA))
                    else:
                        print >>sys.stderr, '\n\nEsse servidor NAO e o lider'
                        log.write("\n\nEsse servidor NAO e o lider")

            except timeout:
                print >>sys.stderr, '\nNenhuma mensagem recebida em 1 segundo, checando se ja passou o tempo para a atualizacao da lista de servidores'
                log.write("\nNenhuma mensagem recebida em 1 segundo")
		log.write("\nChecando o tempo para a atualizacao da lista de servidores\n")
        servidor.socket_recebimento.settimeout(None)

        # Envia Id para atualizar lista de servidores e limpa a propria lista
        mensagem = Mensagem(3, servidor.servidor_id, None, None)
        mensagem_serializada = pickle.dumps(mensagem, 2)
        servidor.socket_recebimento.settimeout(2)
        servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
        print >>sys.stderr, '\n3 segundos se passaram, iniciando processo para atualizar a lista de servidores ativos'
        log.write("\n3 segundos se passaram")
        log.write("\nAtualizando a lista de servidores ativos")
        for servi in servidor.lista_servidores:
            print(time.time() - servi[1])
            if time.time() - servi[1] > 10:
                servidor.lista_servidores.remove(servi)
        print(servidor.lista_servidores)
        servidor.socket_recebimento.settimeout(None)
    log.write("##########################################################\n")  

# Funcao main
if __name__ == '__main__':
    # Abre o arquivo log_servidor em modo de escrita
    log = open("log_servidor.txt","a")

    # Se o arquivo do log de servidores estiver vazio
    if(os.stat("log_servidor.txt").st_size == 0):
    	# Printa o cabecalho no log de execucao
    	log.write("# ==========================================================")
    	log.write("\n# Projeto destinado a disciplina de Redes de Computadores II")
    	log.write("\n# Autores: Lucas Aleixo de Paula e Lucas Olini")
    	log.write("\n# Entrega: 08/06/2018")
    	log.write("\n# ==========================================================\n\n")

    log.write("Endereco IP (TRANSMISSAO): %s\n" % str(ADDRESS))
    print 'Executando o servidor em %s:%d' % (socket.gethostbyname(socket.gethostname()), PORTA_MULTICAST)
    log.write("Porta Transmissao: %s\n" % str(PORTA_MULTICAST))
    log.close()

    # Passa o log e a tabela como parametro para a funcao do servidor
    log = open("log_servidor.txt", "a")
    Servidor_Multicast(log)
    log.close()
