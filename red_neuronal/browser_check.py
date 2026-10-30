"""Prueba funcional real en Chrome; requiere servidor local en 8006."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).parent

def main():
    results=[]; errors=[]; artifacts=ROOT/'.cache/browser';artifacts.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        for width,height in [(1366,768),(1920,1080),(390,844)]:
            context=browser.new_context(viewport=dict(width=width,height=height));page=context.new_page()
            page.on('pageerror',lambda error: errors.append(str(error)))
            response=page.goto('http://127.0.0.1:8006/profesor/red-neuronal.html');assert response.status==200
            expect(page.locator('#activate')).to_be_visible()
            assert context.request.get('http://127.0.0.1:8006/api/parte6/report').status==401
            page.locator('#activate').click();expect(page.locator('#ntrain')).to_have_text('2,520',timeout=60000)
            page.wait_for_function("document.querySelector('#comparison').data?.length === 2")
            assert page.locator('.architecture .layer').count()==4
            assert page.locator('#metrics tr').count()==7
            assert page.locator('#example option').count()==3
            assert page.locator('.js-plotly-plot').count()==3
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Horizontal overflow'
            expected=context.request.get('http://127.0.0.1:8006/api/parte6/report').json()
            assert page.locator('#epoch').inner_text().startswith(str(expected['best_epoch']))
            assert page.evaluate("document.querySelector('#loss').data[0].y")==expected['history']['loss']
            page.locator('#predict').click();expect(page.locator('#prediction')).to_contain_text('Probabilidad neuronal',timeout=30000)
            first=page.locator('#prediction').inner_text()
            page.locator('#example').select_option('1');page.locator('#grade').fill('5');page.locator('#predict').click()
            expect(page.locator('#status')).to_have_text('Predicción calculada por el modelo guardado.')
            page.wait_for_function("!document.getElementById('predict').disabled")
            assert page.locator('#prediction').inner_text()!=first,'Prediction did not update'
            page.evaluate("Plotly.relayout('loss',{'xaxis.range':[1,3]})")
            assert page.evaluate("document.querySelector('#loss').layout.xaxis.range")==[1,3]
            page.locator('#refresh').click();page.wait_for_function("!document.getElementById('refresh').disabled")
            expect(page.locator('#status')).to_contain_text('Resultados cargados')
            page.screenshot(path=str(artifacts/f'{width}x{height}.png'),full_page=True)
            results.append(dict(width=width,height=height,status='passed',checks=15))
            context.close()
        # Backend error must be shown, rather than a silent empty dashboard.
        context=browser.new_context();page=context.new_page();page.goto('http://127.0.0.1:8006/profesor/red-neuronal.html')
        page.route('**/api/parte6/report',lambda route:route.fulfill(status=503,json={'detail':'Modelo no entrenado.'}))
        page.locator('#activate').click();expect(page.locator('#status')).to_have_text('Modelo no entrenado.')
        browser.close()
    assert not errors,errors
    result=dict(viewports=results,error_state='passed',javascript_errors=errors)
    (artifacts/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
