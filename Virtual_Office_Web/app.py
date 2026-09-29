from flask import Flask, render_template, request, jsonify
import pandas as pd
from pathlib import Path
import tempfile, os

app = Flask(__name__)
BASE = Path(__file__).resolve().parent
DEFAULT_FILE = BASE / 'data' / 'Test_Data.xlsx'
current_file = DEFAULT_FILE

def load():
    global current_file
    x = pd.ExcelFile(current_file)
    return {s: pd.read_excel(current_file, sheet_name=s) for s in x.sheet_names}

def money(v): return f"SAR {float(v):,.0f}"

def analysis():
    d=load(); sales=d.get('Sales',pd.DataFrame()); inv=d.get('Inventory',pd.DataFrame()); j=d.get('Journal',pd.DataFrame()); bank=d.get('Bank',pd.DataFrame())
    total=float(sales.get('Sales',pd.Series(dtype=float)).sum())
    gp=float(sales.get('Gross Profit',pd.Series(dtype=float)).sum())
    gp_pct=(gp/total*100) if total else 0
    branches=int(sales['Branch'].nunique()) if 'Branch' in sales else 0
    neg=inv[inv.get('Closing Qty',pd.Series(dtype=float))<0] if not inv.empty and 'Closing Qty' in inv else pd.DataFrame()
    dup_sales=sales[sales.duplicated(subset=['Invoice No'],keep=False)] if 'Invoice No' in sales else pd.DataFrame()
    dup_j=j[j.duplicated(subset=['Voucher No','Account Code','Debit','Credit'],keep=False)] if {'Voucher No','Account Code','Debit','Credit'}.issubset(j.columns) else pd.DataFrame()
    unrecon=bank[bank.get('Difference',pd.Series(dtype=float)).abs()>0.009] if not bank.empty and 'Difference' in bank else pd.DataFrame()
    unusual=j[j.get('Debit',pd.Series(dtype=float))>=30000] if not j.empty and 'Debit' in j else pd.DataFrame()
    by_branch=sales.groupby('Branch',as_index=False).agg(Sales=('Sales','sum'),Gross_Profit=('Gross Profit','sum')) if not sales.empty else pd.DataFrame()
    if not by_branch.empty: by_branch['GP %']=(by_branch['Gross_Profit']/by_branch['Sales']*100).round(1)
    alerts=[]
    if len(neg): alerts.append(f"{len(neg)} negative-stock item(s) need review")
    if len(unrecon): alerts.append(f"{len(unrecon)} bank reconciliation difference(s)")
    if len(dup_sales): alerts.append(f"{len(dup_sales)} sales rows belong to duplicate invoice number(s)")
    if len(dup_j): alerts.append(f"{len(dup_j)} possible duplicate journal line(s)")
    if len(unusual): alerts.append(f"{len(unusual)} unusual debit transaction(s) >= SAR 30,000")
    return {'sales':total,'gp':gp,'gp_pct':gp_pct,'branches':branches,'negative':len(neg),'unrecon':len(unrecon),'dup_sales':len(dup_sales),'dup_journal':len(dup_j),'unusual':len(unusual),'alerts':alerts,'branch':by_branch.to_dict('records')}

@app.route('/')
def home(): return render_template('index.html')

@app.route('/api/summary')
def summary():
    a=analysis(); return jsonify(a)

@app.route('/api/section/<name>')
def section(name):
    a=analysis();
    payload={
      'sales': {'title':'Sales Analysis','lines':[f"Total sales: {money(a['sales'])}",f"Gross profit: {money(a['gp'])}",f"GP margin: {a['gp_pct']:.1f}%"]+[f"{r['Branch']}: {money(r['Sales'])} • GP {r['GP %']:.1f}%" for r in a['branch']]},
      'inventory': {'title':'Inventory','lines':[f"Negative-stock items: {a['negative']}",'Python inventory checks are active.']},
      'finance': {'title':'Finance','lines':[f"Bank reconciliation differences: {a['unrecon']}",'Bank and cash checks are active.']},
      'audit': {'title':'Audit & Compliance','lines':[f"Duplicate sales rows: {a['dup_sales']}",f"Possible duplicate journal lines: {a['dup_journal']}",f"Unusual large debit lines: {a['unusual']}"]},
      'reporting': {'title':'Reports','lines':['Management summary ready from the loaded workbook.',f"Current alerts: {len(a['alerts'])}"]},
      'accounting': {'title':'Accounting','lines':['Trial Balance and Journal sheets loaded.','Accounting checks available through Jaseer.']},
    }
    return jsonify(payload.get(name,payload['reporting']))

@app.route('/api/chat', methods=['POST'])
def chat():
    q=(request.json or {}).get('message','').strip().lower(); a=analysis()
    if not q: return jsonify({'answer':'Type a request for Jaseer.'})
    if 'negative' in q or 'stock' in q or 'inventory' in q: ans=f"Inventory found {a['negative']} negative-stock item(s)."
    elif 'bank' in q or 'recon' in q or 'finance' in q: ans=f"Finance found {a['unrecon']} bank reconciliation difference(s)."
    elif 'duplicate' in q or 'audit' in q: ans=f"Audit found {a['dup_sales']} duplicate sales row(s) and {a['dup_journal']} possible duplicate journal line(s)."
    elif 'sales' in q or 'performance' in q or 'gp' in q: ans=f"Sales are {money(a['sales'])}; gross profit is {money(a['gp'])}; GP margin is {a['gp_pct']:.1f}%."
    elif 'all' in q or 'attention' in q or 'check' in q: ans='Jaseer completed the Python review. ' + ('; '.join(a['alerts']) if a['alerts'] else 'No major exceptions found.')
    else: ans="I’m Jaseer. This web test currently uses Python rules, not an LLM. Ask about sales, GP, inventory, bank reconciliation, duplicates, audit, or what needs attention."
    return jsonify({'answer':ans})

@app.route('/api/upload', methods=['POST'])
def upload():
    global current_file
    f=request.files.get('file')
    if not f or not f.filename.lower().endswith(('.xlsx','.xlsm')): return jsonify({'ok':False,'error':'Please choose an Excel .xlsx/.xlsm file.'}),400
    path=BASE/'uploads'/'current.xlsx'; f.save(path)
    try:
        pd.ExcelFile(path); current_file=path; a=analysis()
        return jsonify({'ok':True,'message':f"Loaded {f.filename}", 'summary':a})
    except Exception as e:
        current_file=DEFAULT_FILE
        return jsonify({'ok':False,'error':str(e)}),400

@app.route('/api/reset', methods=['POST'])
def reset():
    global current_file; current_file=DEFAULT_FILE; return jsonify({'ok':True})

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=True)
