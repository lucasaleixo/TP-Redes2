# ========================================================================
 # Projeto destinado a disciplina de Redes de Computadores II
 # Autores: Lucas Aleixo de Paula e Lucas Olini
 # Entrega: 08/06/2018
 # ======================================================================== 

import socket
import struct
import sys
import pickle

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

# Funcao main
if __name__ == '__main__':
    # Abre o arquivo log_cliente.txt em modo de escrita e printa o cabecalho
    log = open("log_cliente.txt","a")
    log.write("\n# ==========================================================")
    log.write("\n# Projeto destinado a disciplina de Redes de Computadores II")
    log.write("\n# Autores: Lucas Aleixo de Paula e Lucas Olini")
    log.write("\n# Entrega: 08/06/2018")
    log.write("\n# ==========================================================\n")

    # Recebe o endereco, porta e mensagem como parametro
    try:
        addr = sys.argv[1]
        port = int(sys.argv[2])
        numero_1 = float(sys.argv[3])
        operacao = sys.argv[4]
        numero_2 = float(sys.argv[5])

	    # Insere os dados no log de execucao do cliente
        log.write("Endereco: %s\nPorta: %d\nBuffer: %s\n" % (addr,port,str(numero_1) + operacao + str(numero_2)))

    # Se os parametros estiverem incompletos, emite mensagem de erro
    except IndexError:
        print 'use: %s addr port numero_1 operacao numero_2' % sys.argv[0]
        sys.exit(1)

    # Define o socket a ser usado na comunicacao
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    log.write("\nEstabeleceu o socket para comunicacao\n")

    # Define um tempo para o TIMEOUT do socket
    sock.settimeout(0.2)
    log.write("Definiu o timeout do socket para 0.2s\n")

    # Define o TTL como 1, para que as mensagens nao passem do segmento local
    ttl = struct.pack('b', 1)
    log.write("Definiu o TTL para 1\n")

    # Define o grupo MULTICAST para transmitir, usando o TTL definido acima
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    log.write("Definiu o grupo MULTICAST para transmitir\n")

try:
    # Transmite os dados para o grupo MULTICAST
    print >>sys.stderr, 'sending "%s"' % (str(numero_1) + operacao + str(numero_2))
    mensagem = Mensagem(2, None, numero_1, numero_2, operacao, None)
    mensagem_serializada = pickle.dumps(mensagem, 2)
    sent = sock.sendto(mensagem_serializada, (addr, port))
    log.write("\nEnviando: %s\nPara: %s\nPorta: %d\n" % (str(numero_1) + operacao + str(numero_2),addr,port))

    # Procura por respostas de todos os servidores
    while True:
        print >>sys.stderr, 'waiting to receive'
        log.write("Aguardando para receber\n")
        try:
            # Recebe os dados do servidor que respondeu
            data, server = sock.recvfrom(1024)
            mensagem = pickle.loads(data)
            log.write("\nRecebeu: %s\nDe: %s\n" % (mensagem.resultado,server))

        except socket.timeout:
            # Se der timeout, encerra a execucao do cliente
            print >>sys.stderr, 'timed out, no more responses'
            log.write("TIMEOUT\n")
            break
        else:
            # Se receber os dados com sucesso, printa para o usuario
            print >>sys.stderr, 'received "%s" from %s' % (mensagem.resultado, server)

finally:
    # Ao final da execucao, fecha o socket e o arquivo de log
    print >>sys.stderr, 'closing socket'
    log.write("Fechando o socket\n")
    log.close()
    sock.close()
