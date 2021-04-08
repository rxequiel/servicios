import datetime
from posix import NGROUPS_MAX
import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
import time
import pika
import smtplib
import email.message
from envio_email import gmail


class analitica():
    ventana = 15  # Numero de datos pasados que utiliza para realizar los calculos
    pronostico = 1  # Numero de datos a pronosticar
    file_name = "data_base.csv"  # Nombre del archivo CSV
    servidor = "rabbit"  # NPI
    desc = {
        "temperatura": {},
        "humedad": {},
        "presion": {}
    }
    # Diccionario con los datos de analitica descriptiva
    pred = {
        "temperatura": {},
        "humedad": {},
        "presion": {}}  # Diccionario con los datos de analitica predictiva
    # desc={
    #     "temperatura":{
    #         "max":123,
    #         "min":123,
    #         "mean":123,
    #         "median":231,
    #         "std":231,
    #     },
    #     "humedad":{
    #         "max":123,
    #         "min":123,
    #         "mean":123,
    #         "median":231,
    #         "std":231,
    #     },
    #     "presion":{
    #         "max":123,
    #         "min":123,
    #         "mean":123,
    #         "median":231,
    #         "std":231,
    #     },
    # }

    def __init__(self):  # Se Ejecuta al iniciar la clase (o la funcion)
        if self.file_name not in os.listdir(os.getcwd()):
            self.df = pd.DataFrame(columns=["fecha", "sensor", "valor"])
        else:
            self.df = pd.read_csv(self.file_name, index_col=False)

    def update_data(self, msj):
        # print(msj)
        # "temperatura,36.4,humedad,95,presion,1002" Este es el mensaje que manda el micro
        now = datetime.datetime.now()
        date_time = now.strftime('%d.%m.%Y %H:%M:%S')

        msj_vector = msj.split(",")  # Se separa el mensaje por comas
        # ["temperatura","36.4","humedad","95","presion","1002"]

        new_data = [
            {"fecha": date_time,            # 16.03.2021 22:45:00
             "sensor": msj_vector[0],       # temperatura
             "valor": float(msj_vector[1])  # 35.6
             },
            {"fecha": date_time,            # 16.03.2021 22:45:00
             "sensor": msj_vector[2],       # humedad
             "valor": float(msj_vector[3])  # 95
             },
            {"fecha": date_time,            # 16.03.2021 22:45:00
             "sensor": msj_vector[4],       # presion
             "valor": float(msj_vector[5])  # 1003
             }
        ]

        # agregamos los nuevos datos al DF
        self.df = self.df.append(new_data, ignore_index=True)

        self.guardar()  # guardamos el DataFrame en el archivo CSV

        # Enviamos al AMQP el valor de temperatura
        self.publicar(msj_vector[0], msj_vector[1])
        # Enviamos al AMQP el valor de temperatura
        self.publicar(msj_vector[2], msj_vector[3])
        # Enviamos al AMQP el valor de temperatura
        self.publicar(msj_vector[4], msj_vector[5])

        self.analitica_descriptiva(msj_vector)
        self.analitica_predictiva(msj_vector)
        self.alertas(float(msj_vector[1]), float(
            msj_vector[3]), float(msj_vector[5]))

    def analitica_descriptiva(self, msj_vector):
        # Calculando y almacenando las estadisticas de cada sensor
        self.operaciones(msj_vector[0])  # SENSOR DE TEMPERATURA
        self.operaciones(msj_vector[2])  # Sensor de humedad
        self.operaciones(msj_vector[4])  # Sensor de Presion
        # Recorrer el diccionario, Accediendo a cada tipo de sensor
        for sensor in self.desc:
            self.publicar("max-{}".format(sensor),
                          str(self.desc[sensor]["max"]))
            self.publicar("min-{}".format(sensor),
                          str(self.desc[sensor]["min"]))
            self.publicar("mean-{}".format(sensor),
                          str(self.desc[sensor]["mean"]))
            self.publicar("median-{}".format(sensor),
                          str(self.desc[sensor]["median"]))
            self.publicar("std-{}".format(sensor),
                          str(self.desc[sensor]["std"]))

    def operaciones(self, sensor):
        # Filtra en el DF TODOS los datos de sensor
        df_filtrado_todos = self.df[self.df["sensor"] == sensor]
        df_filtrado_valor = df_filtrado_todos["valor"]
        # Filtramos los ultimos n valores del df
        df_filtrado = df_filtrado_valor.tail(self.ventana)
        # Actualizamos almacenando en el diccionario desc las estadisticas del sensor pasado por parametros
        self.desc[sensor].update({
            "max": df_filtrado.max(skipna=True),
            "min": df_filtrado.min(skipna=True),
            "mean": df_filtrado.mean(skipna=True),
            "median": df_filtrado.median(skipna=True),
            "std": df_filtrado.std(skipna=True)
        })

    def analitica_predictiva(self, msj_vector):
        if self.pred == {}:
            self.pred = {
                "temperatura": {"datos": []},
                "humedad": {"datos": []},
                "presion": {"datos": []},
            }
        self.regresion(msj_vector[0])  # temperatura
        self.regresion(msj_vector[2])  # humedad
        self.regresion(msj_vector[4])  # presion
        
        for sensor in self.pred:
            self.publicar("prediccion-{}".format(sensor), "{},{}".format(self.pred[sensor]["datos"][0]["valor"], self.pred[sensor]["datos"][0]["tiempof"]))
                                                            #"33.5,21/03/2121/ 11:03:00"
    def regresion(self, sensor):
        self.pred[sensor]["datos"] = []
        df_filtrado_todos = self.df[self.df["sensor"] == sensor]
        df_filtrado = df_filtrado_todos.tail(self.ventana)
        df_filtrado['fecha'] = pd.to_datetime(
            df_filtrado.pop('fecha'), format='%d.%m.%Y %H:%M:%S')
        df_filtrado['segundos'] = [time.mktime(
            t.timetuple()) - 18000 for t in df_filtrado['fecha']]
        tiempo = df_filtrado['segundos'].std(skipna=True)
        if np.isnan(tiempo):
            return
        tiempo = int(round(tiempo))
        ultimo_tiempo = df_filtrado['segundos'].iloc[-1]
        ultimo_tiempo = ultimo_tiempo.astype(int)
        nuevos_tiempos = np.array(range(
            ultimo_tiempo + tiempo, (self.pronostico + 1) * tiempo + ultimo_tiempo, tiempo))
        X = df_filtrado["segundos"].to_numpy().reshape(-1, 1)
        Y = df_filtrado["valor"].to_numpy().reshape(-1, 1)
        linear_regressor = LinearRegression()
        linear_regressor.fit(X, Y)
        Y_pred = linear_regressor.predict(nuevos_tiempos.reshape(-1, 1))
        

        for tiempo, prediccion in zip(nuevos_tiempos, Y_pred):
            time_format = datetime.datetime.fromtimestamp(tiempo)
            date_time = time_format.replace(tzinfo=datetime.timezone(
                datetime.timedelta(hours=-5))).isoformat()
            self.pred[sensor]["datos"].append({
                "tiempof": date_time,
                "valor": prediccion[0]
            })


    @ staticmethod
    def hallar_max(array, key):
        max = array[0][key]
        for x in array:
            if x[key] > max:
                max = x[key]
        return max

    def alertas(self, temperatura, humedad, presion):
        
        ########### ALERTAS TEMPERATURA ###################
        estado_temp = "normal;"
        pred_temp = self.hallar_max(self.pred["temperatura"]["datos"], "valor")

        ### Valor Actual ##- #
        if temperatura >= 13:
            estado_temp = "El valor actual de temperatura se encuentra por encima de 13°C (el valor maximo recomendable);"
        elif temperatura <= 7:
            estado_temp = "El valor actual de temperatura se encuentra por debajo de 7°C (el valor minimo recomendable);"
        ### Valor Predicho ###
        if pred_temp >= 13:
            estado_temp = estado_temp +  "Se calcula una tendencia de temperatura por encima de 13°C (el valor maximo recomendable)"
        elif pred_temp <= 7:
            estado_temp = estado_temp + "Se calcula una tendencia de temperatura por debajo de 7°C (el valor minimo recomendable)"
        else:
            estado_temp = estado_temp+"normal"

        self.publicar("alerta-temperatura", estado_temp)

        ########### ALERTAS HUMEDAD ###################
        estado_hum = "normal;"
        pred_hum = self.hallar_max(self.pred["humedad"]["datos"], "valor")

        ### Valor Actual ###
        if humedad >= 95:
            estado_hum = "El valor actual de la humedad relativa se encuentra por encima del 95% (el valor maximo recomendable);"
        elif humedad <= 90:
            estado_hum = "El valor actual de la humedad relativa se encuentra por debajo de 90% (el valor minimo recomendable);"
        ### Valor Predicho ###
        if pred_hum >= 95:
            estado_hum = estado_hum + "Se calcula una tendencia de humedad relativa por encima del 95% (el valor maximo recomendable)"
        elif pred_hum <= 90:
            estado_hum = estado_hum + "Se calcula una tendencia de humedad relativa por debajo de 90% (el valor minimo recomendable)"
        else:
            estado_hum = estado_hum+"normal"

        self.publicar("alerta-humedad", estado_hum)

        ########### ALERTAS PRESION ###################
        estado_pres = "normal;"
        pred_hum = self.hallar_max(self.pred["presion"]["datos"], "valor")

        ### Valor Actual ###
        if presion >= 1000:
            estado_pres = "El valor actual de la presion relativa se encuentra por encima del 1000hPa (el valor maximo recomendable);"
        elif presion <= 900:
            estado_pres = "El valor actual de la presion relativa se encuentra por debajo de 900hPa (el valor minimo recomendable);"
        ### Valor Predicho ###
        if pred_hum >= 1000:
            estado_pres = estado_pres + "Se calcula una tendencia de presion por encima del 1000hPa (el valor maximo recomendable)"
        elif pred_hum <= 900:
            estado_pres = estado_pres + "Se calcula una tendencia de presion por debajo de 900hPa (el valor minimo recomendable)"
        else:
            estado_pres = estado_pres + "normal"

        self.publicar("alerta-presion", estado_pres)

    ################# ENVIO EMAIL DE ALERTA #########################
        if (estado_temp != "normal;normal" or estado_hum != "normal;normal" or estado_pres != "normal;normal" ):
            print("Alguna Alerta, Enviando mensaje")
            gmail(estado_temp+"/"+estado_hum+"/"+estado_pres)  # DESCOMENTAR PARA EL ENVIO DE EMAIL
        else: 
            print("Todo Ok")

    @ staticmethod
    def publicar(cola, mensaje):
        connexion = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbit'))
        canal = connexion.channel()
        # Declarar la cola
        canal.queue_declare(queue=cola, durable=True)
        # Publicar el mensaje
        canal.basic_publish(exchange='', routing_key=cola, body=mensaje)
        # Cerrar conexión
        connexion.close()

    def guardar(self):
        try:
            self.df.to_csv(self.file_name, index=False, encoding='utf-8')
        except Exception as error:
            print(error)
