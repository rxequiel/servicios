import datetime
import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
import time
import pika


class analitica():
    ventana = 15
    pronostico = 1
    file_name = "data_base.csv "
    servidor = "rabbit"
    desc = {}  # diccionario con los datos de analitica descriptiva
    pred = {}  # diccionario con los datos de analitica predictiva

    def __init__(self):
        self.load_data()

    def load_data(self):
        if self.file_name not in os.listdir(os.getcwd()):
            self.df = pd.DataFrame(columns=["fecha", "sensor", "valor"])
        else:
            self.df = pd.read_csv(self.file_name, index_col=False)
        # print(self.df)

    # def publicar_antiguos(self):
    #     ant_temp= self.df[self.df["sensor"] == "temperatura"]
    #     ant_hum= self.df[self.df["sensor"] == "humedad"]
    #     ant_pre= self.df[self.df["sensor"] == "presion"]
    #     for index, row in self.df.iterrows():
    #         print(row)

    def update_data(self, msj):
        msj_vetor = msj.split(",")
        now = datetime.datetime.now()
        date_time = now.strftime('%d.%m.%Y %H:%M:%S')

        new_data = [
            {"fecha": date_time,
             "sensor": msj_vetor[0],
             "valor": float(msj_vetor[1])
             },
            {"fecha": date_time,
             "sensor": msj_vetor[2],
             "valor": float(msj_vetor[3])
             },
            {"fecha": date_time,
             "sensor": msj_vetor[4],
             "valor": float(msj_vetor[5])
             }
        ]
        self.df = self.df.append(new_data, ignore_index=True)
        self.guardar()
        self.publicar("temperatura", msj_vetor[1])
        self.publicar("humedad", msj_vetor[3])
        self.publicar("presion", msj_vetor[5])

        self.desc.update(
            {"temperatura": {"actual": {"fecha": date_time, "valor": float(msj_vetor[1])}}})
        self.desc.update(
            {"humedad": {"actual": {"fecha": date_time, "valor": float(msj_vetor[3])}}})
        self.desc.update(
            {"presion": {"actual": {"fecha": date_time, "valor": float(msj_vetor[5])}}})
        # print(self.desc)
        self.analitica_descriptiva()
        self.analitica_predictiva()
        self.alertas(float(msj_vetor[1]),float(msj_vetor[3]))

    def print_data(self):
        print(self.df)

    def alertas(self, temperatura, humedad):

        if "temperatura" not in self.pred:
            self.pred["temperatura"]["alertas"] = 0
        if "alertas" not in self.pred["humedad"]:
            self.pred["humedad"]["alertas"] = 0

        if self.pred["temperatura"]["datos"][0]["valor"] >= 13 or self.pred["temperatura"]["datos"][0]["valor"] <= 7:

            if self.pred["temperatura"]["alertas"] < 5:
                self.pred["temperatura"]["alertas"] = self.pred["temperatura"]["alertas"]+1
            else:
                self.pred["temperatura"]["alertas"] = 0

        if temperatura >= 13 or temperatura <= 7:
            if self.pred["temperatura"]["alertas"] == 5:

                self.publicar("alerta-temperatura", "error,El valor actual de temperatura relativa se encuentra por fuera de los valores recomendados;alerta,Los valores predecidos de temperatura se encuentran por fuera de los valores recomendados")
            else:
                self.publicar(
                    "alerta-temperatura", "error,El valor actual de temperatura relativa se encuentra por fuera de los valores recomendados;")
        else:
            if self.pred["temperatura"]["alertas"] == 5:
                self.publicar(
                    "alerta-temperatura", ";alerta,Los valores predecidos de temperatura se encuentran por fuera de los valores recomendados")
            else:
                self.publicar("alerta-temperatura", "normal,;normal,")

        if self.pred["humedad"]["datos"][0]["valor"] >= 95 or self.pred["humedad"]["datos"][0]["valor"] <= 90:
            if self.pred["humedad"]["alertas"] < 5:
                self.pred["humedad"]["alertas"] = self.pred["humedad"]["alertas"]+1
            else:
                self.pred["humedad"].update(alertas = 0)

        if humedad >= 95 or humedad <= 90:
            if self.pred["humedad"]["alertas"] == 5:
                self.pred["humedad"]["alertas"] = 0
                self.publicar("alerta-humedad", "error,El valor actual de humedad relativa se encuentra por fuera de los valores recomendados;alerta,Los valores predecidos de humedad se encuentran por fuera de los valores recomendados")
            else:
                self.publicar(
                    "alerta-humedad", "error,El valor actual de humedad relativa se encuentra por fuera de los valores recomendados;")
        else:
            if self.pred["humedad"]["alertas"] == 5:
                self.pred["humedad"]["alertas"] = 0
                self.publicar(
                    "alerta-humedad", ";alerta,Los valores predecidos de humedad se encuentran por fuera de los valores recomendados")
            else:
                self.publicar("alerta-humedad", "normal,;normal,")

    def analitica_descriptiva(self):
        self.operaciones("temperatura")
        self.operaciones("humedad")
        self.operaciones("presion")

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
        df_filtrado = self.df[self.df["sensor"] == sensor]
        df_filtrado = df_filtrado["valor"]
        df_filtrado = df_filtrado.tail(self.ventana)
        # if df_filtrado.max(skipna = True) > 34:
        #     self.publicar("alerta/max-{}".format(sensor),"alerta detectada")
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
            for dat in self.pred[sensor]["datos"]:
                self.publicar("prediccion-{}".format(sensor),
                              "{},{}".format(dat["valor"], dat["tiempof"]))

    def regresion(self, sensor):
        if self.pred == {}:
            self.pred = {
                "temperatura": {"datos":[], "alertas":0},
                "humedad": {"datos":[],"alertas":0},
                "presion": {"datos":[], "alertas":0},
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

        self.pred[sensor]["datos"]=[]
        
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
