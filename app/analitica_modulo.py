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
        print(msj)
        # "temperatura,36.4,humedad,95,presion,1002" Este es el mensaje que manda el micro

        msj_vector = msj.split(",")  # Se separa el mensaje por comas
        # ["temperatura","36.4","humedad","95","presion","1002"]
        now = datetime.datetime.now()
        date_time = now.strftime('%d.%m.%Y %H:%M:%S')

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
        self.publicar("temperatura", msj_vector[1])
        # Enviamos al AMQP el valor de temperatura
        self.publicar("humedad", msj_vector[3])
        # Enviamos al AMQP el valor de temperatura
        self.publicar("presion", msj_vector[5])

        self.analitica_descriptiva()
        self.analitica_predictiva()
        self.alertas(float(msj_vector[1]), float(
            msj_vector[3]), float(msj_vector[5]))

    @ staticmethod
    def hallar_max(array, key):
        max = array[0][key]
        for x in array:
            if x[key] > max:
                max = x[key]
        return max

    def alertas(self, temperatura, humedad, presion):

        ########### ALERTAS TEMPERATURA ###################
        alerta_temp = "normal,;"
        pred_temp = self.hallar_max(self.pred["temperatura"]["datos"], "valor")

        ### Valor Actual ###
        if temperatura >= 35:
            alerta_temp = "error,El valor actual de temperatura se encuentra por encima de 13°C (el valor maximo recomendable);"
        elif temperatura <= 30:
            alerta_temp = "error,El valor actual de temperatura se encuentra por debajo de 7°C (el valor minimo recomendable);"
        ### Valor Predicho ###
        if pred_temp >= 35:
            alerta_temp = alerta_temp + \
                "alerta,Se calcula una tendencia de temperatura por encima de 13°C (el valor maximo recomendable)"
        elif pred_temp <= 30:
            alerta_temp = alerta_temp + \
                "alerta,Se calcula una tendencia de temperatura por debajo de 7°C (el valor minimo recomendable)"
        else:
            alerta_temp = alerta_temp+"normal,"

        self.publicar("alerta-temperatura", alerta_temp)

        ########### ALERTAS HUMEDAD ###################
        alerta_hum = "normal,;"
        pred_hum = self.hallar_max(self.pred["humedad"]["datos"], "valor")

        ### Valor Actual ###
        if humedad >= 60:
            alerta_hum = "error,El valor actual de la humedad relativa se encuentra por encima del 95% (el valor maximo recomendable);"
        elif humedad <= 40:
            alerta_hum = "error,El valor actual de la humedad relativa se encuentra por debajo de 90% (el valor minimo recomendable);"
        ### Valor Predicho ###
        if pred_hum >= 60:
            alerta_hum = alerta_hum + \
                "alerta,Se calcula una tendencia de humedad relativa por encima del 95% (el valor maximo recomendable)"
        elif pred_hum <= 40:
            alerta_hum = alerta_hum + \
                "alerta,Se calcula una tendencia de humedad relativa por debajo de 90% (el valor minimo recomendable)"
        else:
            alerta_hum = alerta_hum+"normal,"

        self.publicar("alerta-humedad", alerta_hum)

        ########### ALERTAS PRESION ###################
        alerta_pres = "normal,;"
        pred_hum = self.hallar_max(self.pred["presion"]["datos"], "valor")

        ### Valor Actual ###
        if presion >= 1100:
            alerta_pres = "error,El valor actual de la presion relativa se encuentra por encima del 1000hPa (el valor maximo recomendable);"
        elif presion <= 1000:
            alerta_pres = "error,El valor actual de la presion relativa se encuentra por debajo de 900hPa (el valor minimo recomendable);"
        ### Valor Predicho ###
        if pred_hum >= 1100:
            alerta_pres = alerta_pres + \
                "alerta,Se calcula una tendencia de presion por encima del 1000hPa (el valor maximo recomendable)"
        elif pred_hum <= 1000:
            alerta_pres = alerta_pres + \
                "alerta,Se calcula una tendencia de presion por debajo de 900hPa (el valor minimo recomendable)"
        else:
            alerta_pres = alerta_pres+"normal,"

        self.publicar("alerta-presion", alerta_pres)

    ################# ENVIO EMAIL DE ALERTA #########################
        # gmail(alerta_temp+"/"+alerta_hum+"/"+alerta_pres)  # DESCOMENTAR PARA EL ENVIO DE EMAIL

    def analitica_descriptiva(self):
        # Calculando y almacenando las estadisticas de cada sensor
        self.operaciones("temperatura")
        self.operaciones("humedad")
        self.operaciones("presion")
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
        df_filtrado = self.df[self.df["sensor"] == sensor]
        df_filtrado = df_filtrado["valor"]
        # Filtramos los ultimos n valores del df
        df_filtrado = df_filtrado.tail(self.ventana)
        # almacenamos en el diccionario desc las estadisticas del sensor pasado por parametros
        self.desc[sensor].update({
            "max": df_filtrado.max(skipna=True),
            "min": df_filtrado.min(skipna=True),
            "mean": df_filtrado.mean(skipna=True),
            "median": df_filtrado.median(skipna=True),
            "std": df_filtrado.std(skipna=True)
        })

    def analitica_predictiva(self):
        self.regresion("temperatura")
        self.regresion("humedad")
        self.regresion("presion")
        for sensor in self.pred:
            self.publicar("prediccion-{}".format(sensor), "{},{}".format(
                self.pred[sensor]["datos"][0]["valor"], self.pred[sensor]["datos"][0]["tiempof"]))

    def regresion(self, sensor):
        if self.pred == {}:
            self.pred = {
                "temperatura": {"datos": []},
                "humedad": {"datos": []},
                "presion": {"datos": []},
            }
        df_filtrado = self.df[self.df["sensor"] == sensor]
        df_filtrado = df_filtrado.tail(self.ventana)
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
        range(ultimo_tiempo + tiempo, (self.pronostico + 1)
              * tiempo + ultimo_tiempo, tiempo)
        nuevos_tiempos = np.array(range(
            ultimo_tiempo + tiempo, (self.pronostico + 1) * tiempo + ultimo_tiempo, tiempo))

        X = df_filtrado["segundos"].to_numpy().reshape(-1, 1)
        Y = df_filtrado["valor"].to_numpy().reshape(-1, 1)
        linear_regressor = LinearRegression()
        linear_regressor.fit(X, Y)
        Y_pred = linear_regressor.predict(nuevos_tiempos.reshape(-1, 1))

        self.pred[sensor]["datos"] = []

        for tiempo, prediccion in zip(nuevos_tiempos, Y_pred):
            time_format = datetime.datetime.fromtimestamp(tiempo)
            date_time = time_format.replace(tzinfo=datetime.timezone(
                datetime.timedelta(hours=-5))).isoformat()
            self.pred[sensor]["datos"].append({
                "tiempof": date_time,
                "valor": prediccion[0]
            })

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
