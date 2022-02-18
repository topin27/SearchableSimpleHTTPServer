function doSearch(queryStr) {
  // 清空现有的结果
  let resList = document.getElementById("res_list");
  while (resList.firstChild) {
    resList.removeChild(resList.firstChild);
  }

  // 组装查询 URL
  let queryWords = queryStr.split(" ");
  let queryUrl = "";
  for (let i = 0; i < queryWords.length; i++) {
    if (i === 0) {
      queryUrl += "?dir=test&";
    } else {
      queryUrl += "&";
    }
    queryUrl += "word=";
    queryUrl += queryWords[i];
  }

  let request = new Request(
    "http://127.0.0.1:8000/search" + queryUrl,
    {
      method: "GET",
      credentials: "include",
    }
  );
  fetch(request)
    .then(response => response.json())
    .then(json => {
      for (let i = 0; i < json.length; i++) {
        let item = document.createElement('p');
        item.setAttribute('class', 'res_item');

        let itemTitle = document.createElement('a');
        itemTitle.href = json[i]['file'];
        itemTitle.appendChild(document.createTextNode(json[i]['title']));
        itemTitle.setAttribute('class', 'item_title');
        item.appendChild(itemTitle);

        let itemBr = document.createElement('br');
        item.appendChild(itemBr);

        let itemDesc = document.createTextNode(json[i]['desc']);
        item.appendChild(itemDesc);

        resList.appendChild(item);
      }
    });
}

document.getElementById('search_button').onclick = function () {
  let queryStr = document.getElementById('search_text').value;
  if (!queryStr || queryStr.length === 0) return;

  doSearch(queryStr);
}

document.getElementById('search_text').onkeydown = function (e) {
  e = e || window.event;
  if (e.key == 'Enter') {
    let elem = e.srcElement || e.target;
    let queryStr = elem.value;
    if (!queryStr || queryStr.length === 0) return;

    doSearch(queryStr);
    return false;
  }
};
