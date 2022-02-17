const URL = "http://127.0.0.1:8000/search";

document.getElementById('search_button').onclick = function() {
  let queryStr = document.getElementById('search_text').value;
  if (!queryStr || queryStr.length === 0) return;

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

  let request = new Request(URL + queryUrl, {
    method: "GET",
    credentials: "include",
  });
  fetch(request)
    .then(response => response.json())
    .then(json => {
      for (let i = 0; i < json.length; i++) {
        let li = document.createElement('li');
        li.innerText = json[i]['title'];
        resList.appendChild(li);
      }
    });
}
