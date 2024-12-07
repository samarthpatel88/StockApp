import json
from playwright.sync_api import sync_playwright

def scrape_data(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, timeout=0)

        # Wait for the table to load
        page.wait_for_selector("#DataTables_Table_0")
        print('Starting')

        # Extract data from the table and convert it to a JSON object
        table_data = page.evaluate('''
            () => {
                const rows = Array.from(document.querySelectorAll("#DataTables_Table_0 tbody tr"));
                return rows.map(row => {
                    const cells = Array.from(row.querySelectorAll("td"));
                    return cells.map(cell => cell.innerText);
                });
            }
        ''')
        print('Ending...')
        browser.close()
        return table_data

def convert_to_json(table_data):
    keys = ["Sr#", "StockName", "Code", "Column4", "Changed%"]
    json_data = []
    for row in table_data:
        json_data.append(dict(zip(keys, row)))
    return json.dumps(json_data, indent=4)
