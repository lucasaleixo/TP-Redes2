# ========================================================================
 # Projeto destinado a disciplina de Redes de Computadores II
 # Autores: Lucas Aleixo de Paula e Lucas Olini
 # Entrega: 08/06/2018
 # ======================================================================== 

import socket
import struct
import sys
import pickle

# Endereco e porta para recebimento
ADDRESS = '225.1.1.1'
PORTA_MULTICAST = 3333

# Definicao da porta para resposta
PORTA_RESPOSTA = 4321

# Definicao do objeto Mensagem
class Mensagem(object):
    tipo = None # 1 - Pegar id inicial; 2 - Resposta id inicial; 3 - Pedido Heartbeat; 4 - Resposta Hearbeat ; 5 - Calculo;  6 - Reposta Calculo
    id_servidor = None
    operacao = ""
    resultado = ""

    # Inicializa os atributos da Mensagem
    def __init__(self, tipo, id_servidor=None, operacao=None, resultado=None):
        self.tipo = tipo
        self.id_servidor = id_servidor
        self.operacao = operacao
        self.resultado = resultado

# Funcao main
if __name__ == '__main__':
    # Abre o arquivo log_cliente.txt em modo de escrita e printa o cabecalho
    log = open("log_cliente.txt","a")
    log.write("\n# ==========================================================")
    log.write("\n# Projeto destinado a disciplina de Redes de Computadores II")
    log.write("\n# Autores: Lucas Aleixo de Paula e Lucas Olini")
    log.write("\n# Entrega: 08/06/2018")
    log.write("\n# Log Cliente")
    log.write("\n# ==========================================================\n")

    # Recebe a operacao como parametro
    try:
        operacao = sys.argv[1]

        # Insere os dados no log de execucao do cliente
        log.write("Endereco IP (TRANSMISSAO): %s\n" % str(ADDRESS))
        log.write("Porta de Transmissao: %s\n" % str(PORTA_MULTICAST))
        log.write("Operacao: %s\n" % operacao)

    # Se o parametro estiver incompleto, emite mensagem de erro
    except IndexError:
        print 'ERRO: Formato de entrada incorreto. Deve ser enviada apenas a expressao para ser calculada, sem espacos.'
        sys.exit(1)

    # Define o socket de recebimento, e conecta de acordo com a porta de resposta para o cliente
    socket_recebimento = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    socket_recebimento.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_recebimento.bind(('', PORTA_RESPOSTA))
    print "Estabeleceu o socket para recebimento de mensagens\n"
    log.write("Estabeleceu o socket para recebimento de mensagens\n")

    # Define o socket de envio
    socket_envio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    socket_envio.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 10)
    print "Estabeleceu o socket para envio de mensagens\n"
    log.write("Estabeleceu o socket para envio de mensagens\n")

    # Transmite os dados para o grupo MULTICAST
    mensagem = Mensagem(5, None, operacao, None)
    mensagem_serializada = pickle.dumps(mensagem, 2)
    socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))
    print "Enviando: %s\nPara: %s\nPorta: %d\n" % (operacao, str(ADDRESS), PORTA_MULTICAST)
    log.write("Enviando: %s\nPara: %s\nPorta: %d\n" % (operacao, str(ADDRESS), PORTA_MULTICAST))

    # Define o tempo de TIMEOUT para o socket de recebimento
    socket_recebimento.settimeout(2)
    print "Definiu o timeout da mensagem para 2 segundos\n"
    log.write("Definiu o timeout da mensagem para 2 segundos\n")

    # Procura por respostas de todos os servidores
    while True:
        print 'Aguardando a resposta do calculo...\n'
        log.write("Aguardando a resposta do calculo...\n")

        try:
            # Recebe os dados do servidor que respondeu
            data, server = socket_recebimento.recvfrom(1024)
            mensagem = pickle.loads(data)
            log.write("Recebeu o resultado da operacao\n")
            print "Recebeu o resultado da operacao\n"

            log.write("------------\n")
            log.write("Resultado = %s\nId do servidor que respondeu: %s\n" % (mensagem.resultado, mensagem.id_servidor))
            print 'Resultado = %s\nId do servidor que respondeu: %s\n' % (mensagem.resultado, mensagem.id_servidor)
            log.write("------------\n")
            break

        except socket.timeout:
            # Se der timeout, envia novamente a mensagem pedindo o calculo
            print 'TIMEOUT: Pedido de calculo nao respondido, reenviando a mensagem com a operacao requisitada...\n'
            log.write("TIMEOUT: Pedido de calculo nao respondido, reenviando a mensagem com a operacao requisitada...\n")
            socket_envio.sendto(mensagem_serializada, (ADDRESS, PORTA_MULTICAST))