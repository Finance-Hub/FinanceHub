from fldataapi import IMF
import matplotlib.pyplot as plt

imf = IMF()

# df = imf.dataflow()
# dim_code, dim_codedict = imf.data_structure('DOT')

query_filter = {'CL_FREQ': 'A',
                'CL_AREA_DOT': 'BR',
                'CL_INDICATOR_DOT': 'TXG_FOB_USD',
                'CL_COUNTERPART_AREA_DOT': 'US'}

df = imf.compact_data('DOT', query_filter, 'BR exports to US')

df.plot()
plt.show()
