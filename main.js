const requestURL = 'http://127.0.0.1:5000/';
// const requestURL = 'http://23.254.167.151/udalign/';

// For testing
const parse1 = `# sent_id = n01001013
# text = For those who follow social media transitions on Capitol Hill, this will be a little different.
1	For	for	ADP	IN	_	2	case	2:case	_
2	those	those	PRON	DT	Number=Plur|PronType=Dem	17	obl	4:nsubj|17:obl:for	_
3	who	who	PRON	WP	PronType=Rel	4	nsubj	2:ref	_
4	follow	follow	VERB	VBP	Mood=Ind|Tense=Pres|VerbForm=Fin	2	acl:relcl	2:acl:relcl	_
5	social	social	ADJ	JJ	Degree=Pos	6	amod	6:amod	_
6	media	media	NOUN	NN	Number=Sing	7	compound	7:compound	_
7	transitions	transition	NOUN	NNS	Number=Plur	4	obj	4:obj	_
8	on	on	ADP	IN	_	10	case	10:case	_
9	Capitol	capitol	PROPN	NN	Number=Sing	10	compound	10:compound	_
10	Hill	hill	PROPN	NN	Number=Sing	7	nmod	7:nmod:on	SpaceAfter=No
11	,	,	PUNCT	,	_	17	punct	17:punct	_
12	this	this	PRON	DT	Number=Sing|PronType=Dem	17	nsubj	17:nsubj	_
13	will	will	AUX	MD	VerbForm=Fin	17	aux	17:aux	_
14	be	be	AUX	VB	VerbForm=Inf	17	cop	17:cop	_
15	a	a	DET	DT	Definite=Ind|PronType=Art	16	det	16:det	_
16	little	little	ADJ	JJ	Degree=Pos	17	obl:npmod	17:obl:npmod	_
17	different	different	ADJ	JJ	Degree=Pos	0	root	0:root	SpaceAfter=No
18	.	.	PUNCT	.	_	17	punct	17:punct	_`

const parse2 = `# sent_id = n01001013
# text = Для тех, кто следит за передачей всех материалов, появившихся в социальных сетях о Конгрессе, это будет происходить несколько по-другому.
# text_en = For those who follow social media transitions on Capitol Hill, this will be a little different.
1	Для	_	ADP	IN	_	2	case	_	_
2	тех	_	DET	DT	Animacy=Anim|Case=Gen|Number=Plur	20	obl	_	SpaceAfter=No
3	,	_	PUNCT	,	_	5	punct	_	_
4	кто	_	PRON	WP	Animacy=Anim|Case=Nom|Gender=Masc	5	nsubj	_	_
5	следит	_	VERB	VBC	Aspect=Imp|Mood=Ind|Number=Sing|Person=3|Tense=Pres	2	acl:relcl	_	_
6	за	_	ADP	IN	_	7	case	_	_
7	передачей	_	NOUN	NN	Animacy=Inan|Case=Ins|Gender=Fem|Number=Sing|Person=3	5	obl	_	_
8	всех	_	DET	DT	Animacy=Inan|Case=Gen|Number=Plur	9	det	_	_
9	материалов	_	NOUN	NN	Animacy=Inan|Case=Gen|Gender=Masc|Number=Plur|Person=3	7	nmod	_	SpaceAfter=No
10	,	_	PUNCT	,	_	11	punct	_	_
11	появившихся	_	VERB	VBN	Animacy=Inan|Aspect=Perf|Case=Gen|Number=Plur|Tense=Past|Variant=Long|VerbForm=Part|Voice=Act	9	amod	_	_
12	в	_	ADP	IN	_	14	case	_	_
13	социальных	_	ADJ	JJ	Animacy=Inan|Number=Plur|Variant=Long	14	amod	_	_
14	сетях	_	NOUN	NN	Animacy=Inan|Gender=Fem|Number=Plur|Person=3	11	obl	_	_
15	о	_	ADP	IN	_	16	case	_	_
16	Конгрессе	_	PROPN	NN	Animacy=Inan|Gender=Masc|Number=Sing|Person=3	11	obl	_	SpaceAfter=No
17	,	_	PUNCT	,	_	5	punct	_	_
18	это	_	PRON	DT	Animacy=Inan|Case=Nom|Gender=Neut|Number=Sing	20	nsubj	_	_
19	будет	_	VERB	VBC	Aspect=Imp|Mood=Ind|Number=Sing|Person=3|Tense=Fut	20	aux	_	_
20	происходить	_	VERB	VB	Aspect=Imp	0	root	_	_
21	несколько	_	ADV	RB	_	22	advmod	_	_
22	по-другому	_	ADV	RB	_	20	advmod	_	SpaceAfter=No
23	.	_	PUNCT	.	_	20	punct	_	_`

function chooseCorpus() {
  window.tableName = $('#selectCorpus').val();
  let request = $.get(requestURL + 'getids/' + window.tableName);
  request.done(data => {
    window.sentenceIDs = data;
    $('#sentenceNum').val("1");
    showSentenceByNum();
  });
  request.fail(() => {
    alert('Failed to fetch sentence IDs from the server.');
  });
}

function showSentenceByNum() {
  window.nodeIDs = new Set();
  window.unaligned = new Set();
  window.sentenceNum = parseInt($('#sentenceNum').val());
  let index = window.sentenceNum-1,
      request = $.get(
        requestURL + 
        tableName + '/' +
        window.sentenceIDs[index]['document_id'] + '/' +
        window.sentenceIDs[index]['sentence_id']);
  request.done(data => {
    byID('parse1').innerText = data[0]['en'];
    byID('parse2').innerText = data[0]['ru'];
    window.nodes.clear();
    window.edges.clear();
    addUDParse(data[0]['en'], window.nodes, window.edges, 'top');
    addUDParse(data[0]['ru'], window.nodes, window.edges, 'bottom');
    addAlignment(data[0]['alignment']);
    let verifiedRadios = $('input:radio[name=verified]');
    verifiedRadios.filter('[value=' + data[0]['verified'] + ']').prop('checked', true);
  });
  request.fail(() => {
    alert('Failed to fetch the sentence from the server.');
  });
}

function prevSentence() {
  if (window.sentenceNum > 1) {
    window.sentenceNum--;
    $('#sentenceNum').val(window.sentenceNum);
    showSentenceByNum();
  }
}

function nextSentence() {
  if (window.sentenceNum < 1000) {
    window.sentenceNum++;
    $('#sentenceNum').val(window.sentenceNum);
    showSentenceByNum();
  }
}

function byID(id) {
  return document.getElementById(id);
}

let hOffset = 100,
    vOffset = 200,
    topNodes = new Set(),
    bottomNodes = new Set();

function addUDParse(parseString, nodes, edges, layer) {
  // First pass: create nodes
  let leftOffset = 0,
      lines = parseString.split('\n'),
      i = 0;
  while (lines[i].slice(0, 1) === '#')
    i++;
  let nCommentLines = i;
  while (i < lines.length) {
    let fields = lines[i].split('\t'),
        id = layer+fields[0],
        label = fields[1];
    window.nodeIDs.add(id);
    if (layer === 'top')
      topNodes.add(id);
    else
      bottomNodes.add(id);
    nodes.add({
      id: id,
      label: label,
      // TODO: make adaptive
      x: -1000 + hOffset * (i - nCommentLines),
      y: layer === 'top' ? 0 : vOffset
    });
    i++;
  }
  i = nCommentLines;
  while (i < lines.length) {
    let fields = lines[i].split('\t'),
        id = layer+fields[0],
        edgeLabel = fields[7],
        parent = layer+fields[6];
    if (edgeLabel !== 'root' && edgeLabel !== 'punct') // Ignore punctuation to reduce clutter
      edges.add({
        id: id+'->'+parent,
        arrows: 'from',
        from: id,
        to: parent,
        label: edgeLabel
      });
    i++;
  }
}

function addAlignment(alignmentStr) {
  console.clear();
  window.alignmentArr = [];
  if (alignmentStr === '') {
    return
  }
  console.log(alignmentStr);
  let edgeStrArr = alignmentStr.split(' '),
      ESAlen = edgeStrArr.length;
  for (let i = 0; i < ESAlen; i++) {
    let endpoints = edgeStrArr[i].split('-');
        from = 'top'+(parseInt(endpoints[0])+1),
        to = 'bottom'+(parseInt(endpoints[1])+1);
    if ((endpoints[0] === 'NaN') || (endpoints[1] === 'NaN')) {
      continue
    }
    console.log(endpoints);
    if (endpoints[0] === 'X') {
      console.log('Colouring ', to);
      colourNode(to, contentWordColour);
      window.unaligned.add(to);
    } else if (endpoints[1] === 'X') {
      console.log('Colouring ', from);
      colourNode(from, contentWordColour);
      window.unaligned.add(from);
    } else
      addRemoveEdge(window.edges, from, to);
  }
}

function labelEnd(s) {
  // top3 -> 2
  // bottom1 -> 0
  if (s.charAt(0) === 't')
    return String(parseInt(s.slice('top'.length)) - 1)
  else
    return String(parseInt(s.slice('bottom'.length)) - 1)
}

function updateAlignment() {
  let pharaoStr = null;
  if (window.alignmentArr.length === 0)
    pharaoStr = ''
  else {
    let pharaoArr = window.alignmentArr.map(el => {
      let endpoints = el.split('->'),
          from = parseInt(endpoints[0].substr(3))-1,
          to = parseInt(endpoints[1].substr(6))-1;
      return from+'-'+to
    });
    pharaoStr = pharaoArr.reduce((el1, el2) => el1+' '+el2);
  }
  window.unaligned.forEach(node => {
    let pseudoEdge = (node.charAt(0) === 't') ? (labelEnd(node)+'-X') : ('X-'+labelEnd(node));
    pharaoStr = pharaoStr + ' ' + pseudoEdge;
  });

  console.log(pharaoStr);

  let verified = $("input[name='verified']:checked").val();

  let index = window.sentenceNum-1,
      request = $.post(
        requestURL + 
        tableName + '/' +
        window.sentenceIDs[index]['document_id'] + '/' +
        window.sentenceIDs[index]['sentence_id'],
        data = JSON.stringify({
          alignment: pharaoStr,
          verified: verified
        }));
  request.fail(() => {
    alert('Failed to update data on the server.');
  });
}

function clearAlignment() {
  $.each(window.alignmentArr, (_, edgeID) => {
    edges.remove({id: edgeID});
  });
  window.alignmentArr.splice(0);
}

function clearContentWords() {
  $.each(window.nodes._data, (key, node) => {
    colourNode(key, '#CDDC39');
    window.unaligned.clear();
  })
}

const contentWordColour = 'red';

function colourNode(nodeID, colour) {
  window.nodes.update({
    id: nodeID,
    color: colour
  })
}

function addRemoveEdge(edges, from, to) {
  let edgeID = null;

  // Ignore aligment bugs
  if (!( window.nodeIDs.has(from) && window.nodeIDs.has(to) ))
    return

  // Lexicographically 'topXXX' > 'bottomXXX';
  // 'topXXX' should go first
  if (from > to)
    edgeID = from + '->' + to;
  else
    edgeID = to + '->' + from;

  if (edges._data.hasOwnProperty(edgeID)) {
    let index = window.alignmentArr.indexOf(edgeID);
    window.alignmentArr.splice(index, 1);
    edges.remove({id: edgeID});
  } else {
    edges.add({
      id: edgeID,
      from: from,
      to: to,
      arrows: { to: false },
      smooth: false,
      color: { color:'grey' },
      dashes: true
    });
    window.alignmentArr.push(edgeID);
    colourNode(from, contentWordColour);
    colourNode(to, contentWordColour);
    window.unaligned.delete(from);
    window.unaligned.delete(to);
  }
}

let edgeArr = [];

function clickHandler(params) {
  if (params.nodes.length !== 0) {
    let nodeID = window.network.getNodeAt(params.pointer.DOM);

    // Add/remove edge
    if (edgeArr.length == 0)
      edgeArr.push(nodeID)
    else {
      let oldNodeID = edgeArr[0];
      if ((topNodes.has(nodeID) && topNodes.has(oldNodeID)) ||
          (bottomNodes.has(nodeID) && bottomNodes.has(oldNodeID)))
        edgeArr = [];
      else {
        addRemoveEdge(edges, oldNodeID, nodeID);
        edgeArr = [];
        window.network.unselectAll();
      }
    }
  }
  else
    edgeArr = [];
}

function doubleClickHandler(params) {
  if (params.nodes.length !== 0) {
    let nodeID = window.network.getNodeAt(params.pointer.DOM);
    // Toggle colour for content word
    if (window.nodes._data[nodeID]['color'] === contentWordColour) {
      window.nodes.update({
        id: nodeID,
        color: '#CDDC39'
      });
      window.unaligned.delete(nodeID);
    } else {
      window.nodes.update({
        id: nodeID,
        color: contentWordColour
      });
      window.unaligned.add(nodeID);
    }
  }
}

let nodesArr = [];
window.nodes = new vis.DataSet(nodesArr);
    
let edgesArr = [];
window.edges = new vis.DataSet(edgesArr);

// create a network
let container = byID('mynetwork'),
    data = {
      nodes: window.nodes,
      edges: window.edges
    },
    options = {
      physics:true,
      edges: {
        smooth: {
          type: 'curvedCCW',
          forceDirection: 'vertical'
        }
      },
      nodes: {
        mass: 10,
        fixed: true,
        font: {
          size: 16
        },
        margin: 10,
        color: '#CDDC39'
    },
  };

document.addEventListener("DOMContentLoaded", 
                          (event) => {
  let request = $.get(requestURL + 'corpora');
  request.done(data => {
    $.each(data, (_, val) => {
      $('#selectCorpus').append(
        $('<option>')
        .attr('val', val.name)
        .text(val.name)
        );
    });
    chooseCorpus();
  });
  request.fail(() => { alert('Failed to fetch the list of corpora from the server.') });
  window.network = new vis.Network(container, data, options);
  window.network.on("click", (params) => { clickHandler(params); });
  window.network.on("doubleClick", (params) => { doubleClickHandler(params); });
});
