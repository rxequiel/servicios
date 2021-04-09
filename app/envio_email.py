import smtplib
import email.message


def gmail(mensaje):
    dat = mensaje.split("/")
    # print(dat)
    estados_temp = dat[0].split(";")
    # print(estados_temp)
    estados_hum = dat[1].split(";")
    # print(estados_hum)
    estados_pres = dat[2].split(";")

    out = ""
    cabecera_errores = '''
    <div style="border: solid 1px #f00;border-radius: 4px;background-color: #fff0f5; margin: 5px; padding: 20px; font-size: 20px;">
        <div style="display: inline-flex">
            <img src="https://upload.wikimedia.org/wikipedia/commons/3/3b/Vista-error.png" style="height: 60px">
            <h1 style="color: #f00; margin: auto;margin-left: 20px;"> PELIGRO</h1>
        </div>                
    '''
                
    if estados_temp[0] != 'normal':
        cabecera_errores = cabecera_errores + '<li>' + estados_temp[0].replace("°", "&deg;") + '</li>'
    if estados_hum[0] != 'normal':
        cabecera_errores = cabecera_errores + '<li>' + estados_hum[0] + '</li>'
    if estados_pres[0] != 'normal':
        cabecera_errores = cabecera_errores + '<li>' + estados_pres[0] + '</li>'

    if estados_temp[0] != 'normal' or estados_hum[0] != 'normal' or estados_pres[0] != 'normal':
        out = out + cabecera_errores + '</div>'


    cabecera_alertas = '''<div style="border: solid 1px #ffc700;border-radius: 4px; background-color: #fffacd; margin: 5px;padding: 20px; font-size: 20px;">
                <div style="display: inline-flex">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/OOjs_UI_icon_alert-yellow.svg/800px-OOjs_UI_icon_alert-yellow.svg.png" style="height: 60px">
                    <h1 style="color: #ffc700 ; margin: auto;margin-left: 20px;"> ALERTA </h1>
                </div>'''
    if estados_temp[1] != 'normal':
        cabecera_alertas = cabecera_alertas + '<li>' + estados_temp[1].replace("°", "&deg;") + '</li>'
    if estados_hum[1] != 'normal':
        cabecera_alertas = cabecera_alertas + '<li>' + estados_hum[1] + '</li>'
    if estados_pres[1] != 'normal':
        cabecera_alertas = cabecera_alertas + '<li>' + estados_pres[1] + '</li>'
        
    if estados_temp[1] != 'normal' or estados_hum[1] != 'normal' or estados_pres[1] != 'normal':
        out = out + cabecera_alertas + '</div>'

    # print(out)
    if out == "":
        return

    email_content = """
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        </head>
        <body> """ + out + """
        
        </body>
    </html>    
    """
    msg = email.message.Message()
    msg['Subject'] = 'Alerta del Servidor'

    msg['From'] = "delahoz27montes@gmail.com"  # CORREO REMITENTE ############
    msg['To'] = "javcas430@gmail.com"  # CORREO DESTINO ##############
    password = "montesdelahoz27ezequiel"  # CONTRASEÑA ##################
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(email_content)

    s = smtplib.SMTP('smtp.gmail.com: 587')
    s.starttls()

    # Login Credentials for sending the mail
    s.login(msg['From'], password)

    return s.sendmail(msg['From'], [msg['To']], msg.as_string().encode('ascii', 'ignore'))






