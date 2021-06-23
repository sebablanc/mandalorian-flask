from flask import Flask, render_template, request, redirect, url_for
import redis

app = Flask(__name__)

priceName = 'alquilerValue'
RENTED_STATUS = 'Alquilado'
RESERVED_STATUS = 'Reservado'
AVAILABLE_STATUS = 'Disponible'

statusDic = {
    1: AVAILABLE_STATUS,
    2: AVAILABLE_STATUS,
    3: AVAILABLE_STATUS,
    4: AVAILABLE_STATUS,
    5: AVAILABLE_STATUS,
    6: AVAILABLE_STATUS,
    7: AVAILABLE_STATUS,
    8: AVAILABLE_STATUS
}

def connect_db():
    """Crear conexión a base de datos."""
    conexion = redis.StrictRedis(host='db', port=6379,  db=0)
    if(conexion.ping()):
        conexion.set('alquilerValue', 250)
        print("Conectado al servidor de redis")
    else:
        print("Error...")
    return conexion

@app.route('/')
def home():
    """Retorna la página home."""
    episodes = getEpisodesList()
    verifyStatus()
    return render_template('./home.html', episodes=episodes, status=statusDic)

def verifyStatus():
    conn = connect_db()
    for status in statusDic:
        ttl = conn.ttl(status)
        finded = conn.get(status)
        if (finded and ttl>0):
            statusDic[status] = finded.decode('UTF-8')
        else:
            conn.delete(status)
            statusDic[status] = AVAILABLE_STATUS

def getEpisodesList():
    conn = connect_db()
    return conn.lrange('mandalorian', 0, -1)

def getEpisode(index):
    conn = connect_db()
    episodes = getEpisodesList()
    return episodes[index]

@app.route('/reservar', methods=['POST'])
def reservar():
    print('Se presionó reservar')
    if request.method == 'POST':
        conn = connect_db()
        episode = request.form['episode']
        if(not isReserved(episode)):
            conn.setex(episode, 240, RESERVED_STATUS)
        return redirect(url_for('home'))

def isReserved(episode):
    conn = connect_db()
    finded = conn.get(episode)
    return ((finded != None) and (finded.decode('UTF-8') == RESERVED_STATUS))

def isRented(episode):
    conn = connect_db()
    finded = conn.get(episode)
    return ((finded != None) and (finded.decode('UTF-8') == RENTED_STATUS))

@app.route('/confirmar-pago/<string:episodeToRent>/<string:message>', methods=['GET'])
def confirmarPago(episodeToRent, message):
    print("ConfirmarPago")
    print(episodeToRent)
    if(message == 'null'):
        message = None
    episode = getEpisode(int(episodeToRent)-1)
    print(episode)
    return render_template('./confirmar-pago.html', episode=episode.decode('UTF-8'), episodeNumber=episodeToRent, message=message)

@app.route('/alquilar', methods=['POST'])
def alquilar():
    print('Se presionó alquilar')
    if request.method == 'POST':
        
        #conexión
        conn = connect_db()
        
        #Obteniendo valores
        episode = request.form['episode']
        value = request.form['value']
        price = conn.get(priceName)
        
        #Verifico que el episodio no haya sido rentado
        if isRented(episode):
            message = 'El episodio ya ha sido alquilado'
            return redirect(url_for('confirmarPago', episodeToRent=episode, message=message))
        #Verifico que se haya ingresado un monto
        elif not value or value == '':
            message = 'Proporcione un monto'
            return redirect(url_for('confirmarPago', episodeToRent=episode, message=message))
        #Verifico que el episodio esté reservado y que el monto sea correcto
        elif isReserved(episode) and int(value)==int(price.decode('UTF-8')):
            conn.setex(episode, 1440, RENTED_STATUS)
            return redirect(url_for('home'))
        else:
            message = ''
            if(not isReserved(episode)):
                message = 'Se debe reservar primero el episodio'
            else:
                message = 'Monto incorrecto'
            return redirect(url_for('confirmarPago', episodeToRent=episode, message=message))

if __name__ == '__main__':
    app.run(host='localhost', port='5000', debug=True)