import pandas as pd
import requests

from bokeh.embed import components
from bokeh.models import HoverTool
from bokeh.palettes import d3
from bokeh.plotting import figure
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

STOCK_PLOT_OPTIONS = ['Open', 'High', 'Low', 'Close', 'Adj. Open', 'Adj. High', 'Adj. Low', 'Adj. Close']

STOCK_TOOLTIP_OPTIONS = ['Volume', 'Ex-Dividend', 'Split Ratio', 'Adj. Volume']

class TruthyDataFrame(pd.DataFrame):
    def __bool__(self):
        return False


@app.route('/')
def main():
    return redirect('/index')


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/stocks', methods=['GET', 'POST'])
def stocks():
    if request.method == 'POST':
        f = request.form
        plot_options = ','.join([opt.replace('plt_opt_', '') for opt, _ in f.items() if 'plt_' in opt])
        tooltip_options = ','.join([opt.replace('tt_opt_', '') for opt, _ in f.items() if 'tt_opt' in opt])
        return redirect('/stocks?name={}&plot_options={}&tooltip_options={}'.format(f['Name'], plot_options, tooltip_options))

    elif request.method == 'GET':
        ticker, script, div = '', '', ''
        ticker = request.args.get('name', '')

        plot_options = request.args.get('plot_options')
        tooltip_options = request.args.get('tooltip_options')

        if not plot_options:
            plot_options = ['Close']
        else:
            plot_options = plot_options.split(',')
            
        if not tooltip_options:
            tooltip_options = []
        else:
            tooltip_options = tooltip_options.split(',')

        if ticker:
            colors = d3['Category10'][max(len(plot_options), 3)]
            ticker = ticker.upper()
            quandl_url = 'https://www.quandl.com/api/v3/datasets/WIKI/{}.json'.format(ticker)

            # try:
            quandl = requests.get(quandl_url).json()
            data = quandl['dataset']
            column_names = [cn.replace('-', '').replace(' ', '').replace('.', '') for cn in data['column_names']]

            df = TruthyDataFrame(data['data'], columns=column_names)
            df['Date'] = pd.to_datetime(df['Date'])
            df['date_str'] = df.Date.apply(str)
            df.__bool__ = lambda x: False
            fix_names = [name.replace('-', '').replace(' ', '').replace('.', '') for name in plot_options+tooltip_options+['Date']]
            df = TruthyDataFrame(df.drop([col for col in df.columns if col not in fix_names], axis=1))
            del quandl, data

            tooltips = []
            for index, opt in enumerate(tooltip_options):
                opt_fix = opt.replace('-', '').replace(' ', '').replace('.', '')
                tooltips.append((opt, '@'+opt_fix+'{0,0.000}'))


            print(tooltips)
            hover = HoverTool(tooltips=tooltips)

            plot = figure(plot_height=200, x_axis_type='datetime',
                          tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', hover],
                          x_axis_label='Date and Time',
                          title='{} Historical Market Data'.format(ticker),
                          responsive=True)
            plot.title.align = 'center'
            plot.title.text_font_size = '25px'

            for index, opt in enumerate(plot_options):
                opt_fix = opt.replace('-', '').replace(' ', '').replace('.', '')
                plot.line('Date', opt_fix, source=df, color=colors[index], legend=opt)

            script, div = components(plot)
            # except Exception as e:
            #     print(str(e), ' for error')
            #     div = '<p>ERROR: {} NOT FOUND ON QUANDL'.format(ticker)

    return render_template('stocks.html', ticker=ticker, script=script, div=div,
                           plot_options=STOCK_PLOT_OPTIONS, tooltip_options=STOCK_TOOLTIP_OPTIONS)


@app.route('/crypto', methods=['GET', 'POST'])
def crypto():
    if request.method == 'POST':
        f = request.form
        return redirect('/crypto?name={}'.format(f['Name']))

    elif request.method == 'GET':
        ticker, script, div = '', '', ''
        ticker = request.args.get('name', '')

        if ticker:
            ticker = ticker.upper()
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
                plot = figure(plot_height=200, x_axis_type='datetime',
                              tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', hover],
                              x_axis_label='Date and Time',
                              y_axis_label='Closing Price (BTC)',
                              title='{} Historical Price Data'.format(ticker),
                              responsive=True)
                plot.title.align = 'center'
                plot.title.text_font_size = '25px'

                plot.line('date', 'close', source=df, color='black')

                script, div = components(plot)
            except:
                div = '<p>ERROR: {} IS NOT LISTED ON POLONIEX'.format(ticker)

        return render_template('crypto.html', ticker=ticker, script=script, div=div)


if __name__ == '__main__':
    app.run(port=33507, debug=True)
