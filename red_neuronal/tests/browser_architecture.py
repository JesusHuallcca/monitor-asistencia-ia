"""Comprobación visual y accesible del diagrama, sin modificar el modelo."""
from pathlib import Path
import json,hashlib
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'red_neuronal/.cache/architecture'

def main():
    ART.mkdir(parents=True,exist_ok=True)
    before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'red_neuronal/artifacts').iterdir() if p.is_file()}
    errors=[];results=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        for width,height in [(1366,768),(1920,1080),(390,844)]:
            context=browser.new_context(viewport=dict(width=width,height=height),has_touch=width<700,is_mobile=width<700)
            page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto('http://127.0.0.1:8006/profesor/red-neuronal.html')
            page.locator('#activate').click()
            page.wait_for_function("document.querySelector('#comparison').data?.length===2",timeout=60000)
            expect(page.locator('#architecture .nn-layer')).to_have_count(4)
            expected=[9,32,16,1]
            for i,count in enumerate(expected):
                layer=page.locator(f'.nn-layer[data-layer="{i}"]')
                expect(layer.locator('.nn-neuron')).to_have_count(count)
                expect(layer.locator('.nn-amount strong')).to_have_text(str(count))
                assert layer.bounding_box()['width']>=44
                if width<700:
                    layer.tap();expect(page.locator('#nn-tooltip')).to_be_hidden()
                else:layer.click()
                expect(layer).to_have_attribute('aria-pressed','true')
                expect(page.locator('#nn-detail')).to_have_attribute('data-layer',str(i))
                if i==0:expect(page.locator('#nn-detail .nn-features li')).to_have_count(9)
                else:
                    for text in [('320 parámetros','ReLU'),('528 parámetros','ReLU'),('17 parámetros','sigmoide')][i-1]:expect(page.locator('#nn-detail')).to_contain_text(text)
            expect(page.locator('#nn-detail')).to_contain_text('probabilidad estimada de asistir')
            expect(page.locator('#nn-summary .nn-stat')).to_have_count(4)
            assert page.locator('#nn-summary strong').all_text_contents()==['9','2','1','865']
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Horizontal overflow'
            # Labels and activation captions must fit their own layer at every width.
            assert page.locator('.nn-layer-name,.nn-activation,.nn-stat').evaluate_all('(nodes)=>nodes.every(n=>n.scrollWidth<=n.clientWidth+1 && n.scrollHeight<=n.clientHeight+1)')
            # Keyboard selection and explicit dismissal of the tooltip.
            entry=page.locator('.nn-layer[data-layer="0"]');entry.focus();entry.press('Enter')
            expect(page.locator('#nn-detail .nn-features li')).to_have_count(9)
            entry.press('Tab');page.keyboard.press('Enter')
            expect(page.locator('.nn-layer[data-layer="1"]')).to_have_attribute('aria-pressed','true')
            page.keyboard.press('Escape');expect(page.locator('#nn-tooltip')).to_be_hidden()
            if width>=700:
                entry.hover();expect(page.locator('#nn-tooltip')).to_be_visible()
                expect(page.locator('#nn-tooltip .nn-features li')).to_have_count(9)
                tooltip=page.locator('#nn-tooltip').bounding_box();stage=page.locator('#architecture').bounding_box()
                assert tooltip['y']>=stage['y']+stage['height'],'Tooltip covers diagram'
                assert tooltip['x']>=0 and tooltip['x']+tooltip['width']<=width
                page.locator('.nn-layer[data-layer="2"]').hover();expect(page.locator('#nn-tooltip')).to_contain_text('16 neuronas')
                page.locator('.nn-layer[data-layer="3"]').hover();expect(page.locator('#nn-tooltip')).to_contain_text('Sigmoide')
                page.locator('#nn-title').hover();expect(page.locator('#nn-tooltip')).to_be_hidden()
            # Other graphs and live inference still work with the redesigned architecture.
            assert page.locator('.js-plotly-plot').count()==3
            page.locator('#predict').click();expect(page.locator('#prediction')).to_contain_text('Probabilidad neuronal',timeout=30000)
            entry.click();page.mouse.move(0,0)
            expect(page.locator('#nn-tooltip')).to_be_hidden()
            page.locator('.nn-card').screenshot(path=str(ART/f'{width}x{height}-diagrama.png'))
            page.screenshot(path=str(ART/f'{width}x{height}-dashboard.png'),full_page=True)
            results.append(dict(width=width,height=height,neurons=sum(expected),layers=4,selection='passed',keyboard='passed',tooltip='passed' if width>=700 else 'touch passed',overflow=False))
            context.close()
        browser.close()
    assert not errors,errors
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in before.items()),'A protected file changed'
    result=dict(viewports=results,javascript_errors=errors,protected_files_unchanged=len(before))
    (ART/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
