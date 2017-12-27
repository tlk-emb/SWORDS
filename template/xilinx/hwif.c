#pragma HLS INTERFACE s_axilite port=return
{%- for (n,m,o,b) in zip(name,mode,offset,bundle): %}
{%- if (o==None) and (b==None): %}
#pragma HLS INTERFACE {{ m }} port={{ n }}
{%- elif (o==None): %}
#pragma HLS INTERFACE {{ m }} port={{ n }} bundle={{ b }}
{%- elif (b==None): %}
#pragma HLS INTERFACE {{ m }} port={{ n }} offset={{ o }}
{%- else %}
#pragma HLS INTERFACE {{ m }} port={{ n }} offset={{ o }} bundle={{ b }}
{%- endif %}
{%- endfor %}
