import smtplib
import email.message


def format_msg(msg):
    x1 = ""
    x2 = ""
    if (msg.split(";")[0].split(",")[0] == "error"):
        x1 = msg.split(";")[0].split(",")[1]

    if (msg.split(";")[1].split(",")[0] == "alerta"):
        x2 = msg.split(";")[1].split(",")[1]

    return x1+";"+x2


def gmail(mensaje):

    dat = mensaje.split("/")
    # print(dat)
    dat1 = format_msg(dat[0]).split(";")
    # print(dat1)
    dat2 = format_msg(dat[1]).split(";")
    # print(dat2)
    dat3 = format_msg(dat[2]).split(";")

    out = ""
    x1 = '''<div style="border: solid 1px #f00;border-radius: 4px;background-color: #fff0f5; margin: 5px; padding: 20px; font-size: 20px;">
                <div style="display: inline-flex">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/3/3b/Vista-error.png" style="height: 60px">
                    <h1 style="color: #f00; margin: auto;margin-left: 20px;"> PELIGRO</h1>
                </div>'''
    x2 = '''<div style="border: solid 1px #ffc700;border-radius: 4px; background-color: #fffacd; margin: 5px;padding: 20px; font-size: 20px;">
                <div style="display: inline-flex">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/OOjs_UI_icon_alert-yellow.svg/800px-OOjs_UI_icon_alert-yellow.svg.png" style="height: 60px">
                    <h1 style="color: #ffc700 ; margin: auto;margin-left: 20px;"> ALERTA </h1>
                </div>'''
    if dat1[0] != '':
        x1 = x1 + '<li>' + dat1[0].replace("°", "&deg;") + '</li>'
    if dat2[0] != '':
        x1 = x1 + '<li>' + dat2[0] + '</li>'
    if dat3[0] != '':
        x1 = x1 + '<li>' + dat3[0] + '</li>'

    if dat1[1] != '':
        x2 = x2 + '<li>' + dat1[1].replace("°", "&deg;") + '</li>'
    if dat2[1] != '':
        x2 = x2 + '<li>' + dat2[1] + '</li>'
    if dat3[1] != '':
        x2 = x2 + '<li>' + dat3[1] + '</li>'

    if dat1[0] != '' or dat2[0] != '' or dat3[0] != '':
        out = out + x1 + '</div>'

    if dat1[1] != '' or dat2[1] != '' or dat3[1] != '':
        out = out + x2 + '</div>'

    # print(out)

    email_content = """
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        </head>
        <body>""" + out + """
        
        </body>
    </html>    
    """
    msg = email.message.Message()
    msg['Subject'] = 'Alerta del Servidor'

    msg['From'] = 'delahoz27montes@gmail.com'  # CORREO REMITENTE ############
    msg['To'] = 'delahoz27montes@gmail.com'  # CORREO DESTINO ##############
    password = "montesdelahoz27ezequiel"  # CONTRASEÑA ##################
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(email_content)

    s = smtplib.SMTP('smtp.gmail.com: 587')
    s.starttls()

    # Login Credentials for sending the mail
    s.login(msg['From'], password)

    return s.sendmail(msg['From'], [msg['To']], msg.as_string().encode('ascii', 'ignore'))
