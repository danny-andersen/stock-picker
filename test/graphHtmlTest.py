import plotly.express as px
from pandas import DataFrame
from datetime import datetime
from domonic.html import *


gaindict = {'Date': [datetime(month=11, day=10, year=2022), datetime(month=10, day=9, year=2022), datetime(month=9, day=8, year=2022),datetime(month=8, day=7, year=2022), datetime(month=7, day=6, year=2022)   ],
            'Account Gain' : [13, 11, 10, 12, 8],
            'FUND' : [5, 3, 6, 8, 2]}
df = DataFrame(gaindict)
# df = px.data.stocks()
fig = px.line(df, x="Date", y=df.columns,
              hover_data={"Date": "|%B %d, %Y"},
              title='Account gain by asset type',
              labels={'value': '% Gain'})
fig.update_xaxes(
    dtick="M1",
    tickformat="%b\n%Y")
fig.show()
dom = body()
dom.appendChild(h1("Historic performance"))
dom.appendChild(fig.to_html())

ht = html(meta(_charset='UTF-8'))
ht.append(dom)
retStr = f"{ht}"
text_file = open("exampleHtml/htmlgraph.html", "w+t")
n = text_file.write(retStr)
text_file.close()
