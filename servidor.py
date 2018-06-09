# ========================================================================
 # Projeto destinado a disciplina de Redes de Computadores II
 # Autores: Lucas Aleixo de Paula(GRR20153408) e Lucas Olini(GRR20157108)
 # Entrega: 08/06/2018
 # ======================================================================== 

import socket
from socket import timeout
import struct
import sys
import os
import pickle
import time
import random

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

        # Define o socket de recebimento, e conecta de acordo com a porta do multicast
        self.socket_recebimento = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket_recebimento.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_recebimento.bind(('', PORTA_MULTICAST))

        # Define o grupo MULTICAST, e adiciona o servidor ao grupo de MULTICAST
        mreq = struct.pack('4sl', socket.inet_aton(ADDRESS), socket.INADDR_ANY)
        self.socket_recebimento.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print "Estabeleceu o socket para recebimento de mensagens\n"
        log.write("\nEstabeleceu o socket para recebimento de mensagens\n")

        # Define o socket de envio
        self.socket_envio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket_envio.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)
        print "Estabeleceu o socket para envio de mensagens\n"
        log.write("\nEstabeleceu o socket para envio de mensagens\n")

# Funcao principal do servidor
def Servidor_Multicast(log):
    # Inicia a lista de servidores vazia
    servidor = Servidor([], None)
    print("Inicializando servidor sem Id e com lista de servidores vazia\n")
    log.write("\nInicializando servidor sem ID e com a lista de servidores vazia\n")

    # Mensagem inicial do tipo 1, para definir os IDs
    mensagem = Mensagem(1, None, None, None)
    mensagem_serializada = pickle.dumps(mensagem, 2)
    maior_id = 0

    # Define o timeout para o socket e transmite na PORTA_MULTICAST
    servidor.socket_recebimento.settimeout(2)
    servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
    print "Enviando mensagem pedindo o Id dos outros servidores para popular a lista de servidores\n"
    log.write("\nEnviando mensagem pedindo o ID dos outros servidores para popular a lista de servidores\n")

    print "Aguardando 5 segundos para popular a lista...\n"
    log.write("\nAguardando 5 segundos para popular a lista...\n")
    time_end = time.time() + 5
    # Loop para compor a lista de servidores. Rodando no maximo por 5 segundos
    while time_end > time.time():
        try:
	        # Recebe os dados atraves do socket de recebimento
            data, addr = servidor.socket_recebimento.recvfrom(1024)
            mensagem = pickle.loads(data)

	        # Se o tipo da mensagem for 2, verifica o ID
            if mensagem.tipo == 2:
                if mensagem.id_servidor != None:
                    # Verifica se este ID ja existe na lista de servidores disponiveis
                    if any(mensagem.id_servidor in servidor for servidor in servidor.lista_servidores):
                        pass
                    else:
    		            # Compara o ID do servidor com o maior ID
                        if maior_id < mensagem.id_servidor:
                            maior_id = mensagem.id_servidor

    		            # Adiciona o servidor a lista de servidores
                        servidor.lista_servidores.append([mensagem.id_servidor, time.time()])
                        print "Recebeu Id = %s. Colocando este servidor na lista de servidores disponiveis\n" % mensagem.id_servidor
                        log.write("\nRecebeu ID = %s. Colocando este servidor na lista de servidores disponiveis\n" % mensagem.id_servidor)
	   # Se houver timeout, envia novamente. Se terminou o tempo de recebimento inicial, sai do loop
        except timeout:
            if time_end > time.time():
                servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
          
    servidor.socket_recebimento.settimeout(None)

    # Printa a lista de servidores
    print "\nLista de Servidores Disponiveis: " + servidor.lista_servidores
    log.write("\nLista de Servidores Disponiveis: " + servidor.lista_servidores)

    # Se o maior ID nao for 0, a lista nao esta vazia
    if (maior_id != 0):
        # Atribuindo id do servidor
        print '\nJa existem outros servidores no grupo Multicast, atribuindo id = %s ao servidor' % str(maior_id + 1)
        log.write('\nJa existem outros servidores no grupo Multicast, atribuindo id = %s ao servidor' % str(maior_id + 1))
        servidor.servidor_id = maior_id + 1

    # Se o maior ID for 0, a lista esta vazia
    elif (maior_id == 0):
    	log.write("\n##########################################################\n")
        # Ainda nao tem nenhum servidor, este vai ser o servidor 1
        print '\nNenhum servidor encontrado, atribuindo id 1 ao servidor'
        log.write("\nNenhum servidor encontrado, atribuindo o ID 1 ao servidor\n")
        servidor.servidor_id = 1

    # Envia mensagem indicando aos outros servidores que entrou no grupo Multicast
    mensagem = Mensagem(3, servidor.servidor_id, None, None)
    mensagem_serializada = pickle.dumps(mensagem, 2)
    servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
    log.write("##########################################################\n\n")

    # Loop de requisicoes e respostas
    while True:
        # Escuta no endereco e porta passados como parametro
        print '\nAguardando o recebimento de alguma mensagem...\n'
        log.write('\nAguardando o recebimento de alguma mensagem...\n')

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
                    print "\nNovo servidor entrando na rede, enviando o id deste servidor(ID = %s)\n" % str(servidor.servidor_id)
                    log.write("\nNovo servidor entrando na rede, enviando o id deste servidor(ID = %s)\n" % str(servidor.servidor_id))

                # Mensagem de Heartbeat
                elif (mensagem.tipo == 3):
                    if (mensagem.id_servidor != None):
                        if (mensagem.id_servidor != servidor.servidor_id):
                            servidor_novo = True
                            print "\nRecebeu mensagem de Heartbeat, checando se o servidor enviado ja esta na lista de servidores...\n"
                            log.write("\nRecebeu mensagem de Heartbeat, checando se o servidor enviado ja esta na lista de servidores...\n")
                            for serv in servidor.lista_servidores:
                                if serv[0] == mensagem.id_servidor:
                                    print "\nServidor %s ja existente na lista, atualizando timestamp\n" % mensagem.id_servidor
                                    log.write("\nServidor %s ja existente na lista, atualizando timestamp\n" % mensagem.id_servidor)
                                    serv[1] = time.time()
                                    servidor_novo = False
                            if servidor_novo:
                                print "\nServidor %s novo, adicionando a lista de servidores\n" % mensagem.id_servidor
                                log.write("\nServidor %s novo, adicionando a lista de servidores\n" % mensagem.id_servidor)
                                servidor.lista_servidores.append([mensagem.id_servidor, time.time()])
                    print "Lista de servidores disponiveis: " + servidor.lista_servidores
                    log.write("Lista de servidores disponiveis: " + servidor.lista_servidores)

                # Calculo
                elif (mensagem.tipo == 5):
		    log.write("\nRecebeu um pedido de calculo do cliente, expressao: %s\n" % mensagem.operacao)
                    servidor_lider = True

		    # Identifica o servidor lider para responder
                    for serv in servidor.lista_servidores:
                        if serv[0] < servidor.servidor_id:
                            servidor_lider = False
                            break

		    # Se for o lider, envia o resultado do calculo
                    if servidor_lider:
                        log.write("\n\nServidor lider identificado, ID = %s" % servidor.servidor_id)
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
                        print '\nEnviando resultado do calculo para o cliente.\nResultado = %s \n' % resultado_calculo
                        log.write("\nEnviando resultado do calculo para o cliente.\nResultado = %s \n" % resultado_calculo)
                        mensagem = Mensagem(6, servidor.servidor_id, None, resultado_calculo)
                        mensagem_serializada = pickle.dumps(mensagem, 2)
                        servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_RESPOSTA))
                    else:
                        print >>sys.stderr, '\n\nEsse servidor NAO e o lider'
                        log.write("\n\nEsse servidor NAO e o lider")

            except timeout:
                print '\nNenhuma mensagem recebida em 1 segundo, checando se ja passou o tempo para envio do heartbeat e limpeza da lista de servidores\n'
                log.write('\nNenhuma mensagem recebida em 1 segundo, checando se ja passou o tempo para envio do heartbeat e limpeza da lista de servidores\n')
        servidor.socket_recebimento.settimeout(None)

        # Envia Id para atualizar lista de servidores e limpa a propria lista
        mensagem = Mensagem(3, servidor.servidor_id, None, None)
        mensagem_serializada = pickle.dumps(mensagem, 2)
        servidor.socket_recebimento.settimeout(2)
        servidor.socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
        print '\n3 segundos se passaram, enviando mensagem de heartbeat'
        log.write('\n3 segundos se passaram, enviando mensagem de heartbeat')
        for servi in servidor.lista_servidores:
            print(time.time() - servi[1])
            if time.time() - servi[1] > 10:
                print "Servidor ID = %s inativo por mais de 10 segundos, removendo o mesmo da lista de servidores\n" % servi[0]
                log.write("Servidor ID = %s inativo por mais de 10 segundos, removendo o mesmo da lista de servidores\n" % servi[0])
                servidor.lista_servidores.remove(servi)
        print "Lista de servidores disponiveis: " + servidor.lista_servidores
        log.write("Lista de servidores disponiveis: " + servidor.lista_servidores)
        servidor.socket_recebimento.settimeout(None)
    log.write("##########################################################\n")  

# Funcao main
if __name__ == '__main__':
    randomico = random.randrange(0,10)
    # Abre o arquivo log_servidor em modo de escrita
    log = open("log_servidor"+str(randomico)+".txt","a")

    # Se o arquivo do log de servidores estiver vazio
    if(os.stat("log_servidor"+str(randomico)+".txt").st_size == 0):
    	# Printa o cabecalho no log de execucao
    	log.write("# ==========================================================")
    	log.write("\n# Projeto destinado a disciplina de Redes de Computadores II")
    	log.write("\n# Autores: Lucas Aleixo de Paula(GRR20153408) e Lucas Olini(GRR20157108)")
    	log.write("\n# Entrega: 08/06/2018")
    	log.write("\n# ==========================================================\n\n")

    log.write("ENDERECO_IP (TRANSMISSAO): %s\n" % str(ADDRESS))
    print 'Executando o servidor em %s:%d' % (socket.gethostbyname(socket.gethostname()), PORTA_MULTICAST)
    log.write("PORTA_MULTICAST: %s\n" % str(PORTA_MULTICAST))
    log.close()

    # Passa o log e a tabela como parametro para a funcao do servidor
    log = open("log_servidor"+str(randomico)+".txt", "a")
    Servidor_Multicast(log)
    log.close()
