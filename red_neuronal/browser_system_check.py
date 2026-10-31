"""Chrome contra una API SQLAlchemy/JWT REAL de prueba en SQLite RAM; NO prueba MySQL."""
from pathlib import Path
import json,os
from playwright.sync_api import sync_playwright,expect
ART=Path(__file__).parent/'.cache/integracion/browser'

def main():
    ART.mkdir(parents=True,exist_ok=True);results=[];errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        for width,height in [(1366,768),(1920,1080),(390,844)]:
            ctx=browser.new_context(viewport=dict(width=width,height=height));p=ctx.new_page();expect.set_options(timeout=30000);p.on('pageerror',lambda error:errors.append(str(error)))
            p.goto(os.getenv('PARTE6_TEST_URL','http://127.0.0.1:8008')+'/profesor/red-neuronal.html');expect(p.locator('#system-login')).to_be_visible()
            p.locator('#system-user').fill('fixture-1');p.locator('#system-password').fill('solo-fixture-local');p.locator('#system-login button').click()
            expect(p.locator('#system-course option')).to_have_count(2,timeout=30000)
            assert p.locator('#system-password').input_value()==''
            p.locator('#system-course').select_option('1');expect(p.locator('#system-student option')).to_have_count(3)
            p.locator('#system-student').select_option('1');p.locator('#system-context').click()
            expect(p.locator('#system-predict')).to_be_enabled();expect(p.locator('#system-features>div')).to_have_count(9)
            expect(p.locator('#system-history tr')).to_have_count(7)
            with p.expect_response('**/api/parte6/system/predict',timeout=120000) as response:p.locator('#system-predict').click()
            data=response.value.json();expect(p.locator('#system-prediction')).to_contain_text('Probabilidad experimental')
            assert 0<=data['probabilidad']<=1 and data['features']['promedio_previo']==14
            assert p.locator('.notice').inner_text().startswith('PRUEBA AUTOMÁTICA CON SQLITE')
            assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
            p.screenshot(path=str(ART/f'{width}x{height}-system.png'),full_page=True)
            p.locator('#system-student').select_option('2');expect(p.locator('#system-prediction')).to_be_hidden()
            p.locator('#system-context').click();expect(p.locator('#system-predict')).to_be_disabled()
            expect(p.locator('#system-blockers')).to_contain_text('Falta un estado explícito')
            p.screenshot(path=str(ART/f'{width}x{height}-insuficiente.png'),full_page=True)
            p.locator('#mode-demo').click();expect(p.locator('#demo-examples')).to_be_visible(timeout=60000)
            p.locator('#predict').click();expect(p.locator('#prediction')).to_contain_text('Probabilidad neuronal')
            assert p.locator('.js-plotly-plot').count()==3
            results.append(dict(width=width,height=height,api='SQLAlchemy SQLite RAM + JWT real de prueba',system_prediction='passed',insufficient='passed',synthetic='passed',overflow=False))
            ctx.close()
        browser.close()
    assert not errors,errors
    result=dict(viewports=results,javascript_errors=errors,mysql_connection='not_executed')
    (ART/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(result,ensure_ascii=True))
if __name__=='__main__':main()
