const puppeteer = require('puppeteer');
const low = require('lowdb');
const FileSync = require('lowdb/adapters/FileSync');

const adapter = new FileSync('di.json');
const db = low(adapter);

function wait (ms) {
    return new Promise(resolve => setTimeout(() => resolve(), ms));
}

console.log('\033[2J');
console.log('   -- Data Crawler - B3 DI tax --   ', '\n');
console.log('Crawling into B3 page...', '\n')

let b3Url = 'http://www.b3.com.br/pt_br/';
(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 926 });
  await page.goto(b3Url, {waitUntil: 'load'});
  await wait(30000);

  let b3Data = await page.evaluate(() => {
    let vals = [];
    let b3Elms = document.querySelectorAll('div.cards');
    b3Elms.forEach(el => {
      let jubs = {};
        try{
            jubs.dt = el.querySelector('div.data').innerText;
            jubs.val = el.querySelector('div.valor').innerText;
        }
        catch (exception){}
        vals.push(jubs);
      });
      return vals;
    })
    let b3_data = b3Data;
    console.log('B3 website data: ', '\n');
    console.dir(b3_data);
    console.log('\n');

    // Database phase

    let cetip_date = '2018' + '-' + b3_data[1]['dt'].substring(3,6) + '-' + b3_data[1]['dt'].substring(0,2);
    let cetip_taxa = b3_data[1]['val'].substring(0,1) + '.' + b3_data[1]['val'].substring(2,4);

    const val = db.get('di')
                    .last()
                    .value()
    if(val['Data'] == cetip_date){
        console.log('Data already in database');
    }
    else{
        id_ = val['id'] + 1;
        db.get('di')
            .push({id: id_, Data: cetip_date, DI: cetip_taxa})
            .write()
        out_str = "Data " + "{ " + cetip_date + ' , ' + cetip_taxa + " }" + " insert successful";
        console.log(out_str);
    }
})();
