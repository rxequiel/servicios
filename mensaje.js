var msg_out = { payload: "" }
var dat = msg.payload.split("/")
var dat1 = dat[0].split(";")
var dat2 = dat[1].split(";")
var out = ""
var x1 = '<div style="border: solid 1px #f00;border-radius: 4px;background-color: #fff0f5; margin: 5px; padding: 20px; font-size: 20px;"><div style="display: inline-flex"><img src="https://www.iconsdb.com/icons/preview/red/error-5-xxl.png" style="height: 60px"> <h1 style="color: #f00; margin: auto;margin-left: 20px;"> PELIGRO</h1></div>'
var x2 = '<div style="border: solid 1px #ffc700;border-radius: 4px;    background-color: #fffacd; margin: 5px;padding: 20px; font-size: 20px;"><div style="display: inline-flex"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/OOjs_UI_icon_alert-yellow.svg/800px-OOjs_UI_icon_alert-yellow.svg.png" style="height: 60px"> <h1 style="color: #ffc700 ; margin: auto;margin-left: 20px;"> ALERTA </h1></div>'
if (dat1[0] != ''){
    x1 = x1.concat('<li>', dat1[0], "</li>")
}
if (dat2[0] != ''){
    x1 = x1.concat("<li>", dat2[0], "</li>")
}
if (dat1[1] != ''){
    x2 = x2.concat('<li>', dat1[1], "</li>")
}
if (dat2[1] != ''){
    x2 = x2.concat("<li>", dat2[1], "</li>")
}
if (dat1[0]!= '' || dat2[0]!= ''){
    out=out.concat(x1,"</div>")
}
if (dat1[1]!= '' || dat2[1]!= ''){
    out=out.concat(x2,"</div>")
}
msg_out.payload = out
return msg_out