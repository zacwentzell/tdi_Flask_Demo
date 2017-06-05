import pandas as pd
import requests

from bokeh.embed import components
from bokeh.models import HoverTool
from bokeh.plotting import figure
from flask import Flask, render_template, request, redirect

app = Flask(__name__)


@app.route('/')
def main():
    return redirect('/index')


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/stocks')
def stocks():
    return render_template('stocks.html')


@app.route('/crypto')
def crypto():
    script, div = '', ''
    ticker = request.args.get('name').upper()

    if ticker:
        poloniex_url = 'https://poloniex.com/public?command=returnChartData&currencyPair=BTC_{}&start=1435699200&end=9999999999&period=86400'

        try:
            data = requests.get(poloniex_url.format(ticker)).json()
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'], unit='s')
            df['date_str'] = df.date.apply(str)

            hover = HoverTool(tooltips=[('Time', '@date_str'),
                                        ('Opening Price', '@open{0.00000000}'),
                                        ('Closing Price', '@close{0.00000000}'),
                                        ('Low|High', '@low{0.00000000}|@high{0.00000000}')
                                        ])
            plot = figure(plot_height=100, x_axis_type='datetime',
                          tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', hover],
                          x_axis_label='Date and Time',
                          y_axis_label='Closing Price',
                          responsive=True)

            plot.line('date', 'close', source=df, color='black')

            script, div = components(plot)
        except:
            div = '<p>{} IS NOT LISTED ON POLONIEX'.format(ticker)

    return render_template('crypto.html', script=script, div=div)


@app.route('/crypto_pick', methods=['POST'])
def crypto_pick():
    f = request.form
    return redirect('/crypto?name={}'.format(f['Name']))


if __name__ == '__main__':
    app.run(port=33507)
