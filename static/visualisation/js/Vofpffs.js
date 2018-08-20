/**
 * Copyright (C) David Monteiro @starkids12
 * Original repo available at https://github.com/starkids12/ba_Vofpffs
 *
 * Used with permission.
 * Slightly adapted to work with PrivacyService.
 */

// control the Visualisation
var selectedVisualiation = "";
var selectedProperty = "";

// html Elements
var visualSelector;
var propertySelector;

// html Elements for displaying FileEntry data
var idp;
// var filenamep;
var sizep;
var ipp;
var datep;
var headerl;

var parse = d3.utcParse("%Y-%m-%d %H:%M:%S.%f");
var formatTime = d3.utcFormat("%B %d, %Y");
var color = d3.scaleOrdinal(d3.schemeCategory10);


function initMap() {
    //todo: Setting Map Center dynamically
};

// Getting the HTML Elements
$(document).ready(function () {

    idp = document.getElementById("idParagraph");
    // filenamep = document.getElementById("filenameParagraph");
    sizep = document.getElementById("sizeParagraph");
    ipp = document.getElementById("ipParagraph");
    datep = document.getElementById("dateParagraph");
    headerl = document.getElementById("HeaderList");
    // countryp = document.getElementById("countryParagraph");
    // regionNamep = document.getElementById("regionNameParagraph");
    // cityp = document.getElementById("cityParagraph");
    // latp = document.getElementById("latParagraph");
    // lonp = document.getElementById("lonParagraph");
    // ispp = document.getElementById("ispParagraph");

    visualSelector = document.getElementById("visualSelector");
    propertySelector = document.getElementById("propertySelector");

    renderChart();
});

// New Window Size requires re rendering of the Visualization to fit the screen
$(window).resize(function () {

    renderChart();
});

// new Visualisation has been selected
function onVisualChange(select) {

    selectedVisualiation = select;
    renderChart();
    resetInspector();
};

// new Property to display has been selected
function onPropertyChange(select) {
    selectedProperty = select;
    renderChart();
    resetInspector();
};

// hide/show the property selector
function setPropertySelector(display) {
    propertySelector.style.display = display;
}

// render the Visualisation
function renderChart() {
    setSelectorFields({});

    d3.json("/storage/v1/dump", function (error, data) {
        if (error)
            throw error;

        if (selectedVisualiation == "") {
            selectedVisualiation = "treeMap";
            selectedProperty = "key";
            setPropertySelector("block");
        }

        if (selectedVisualiation == "treeMap") {
            renderTreemap(data, selectedProperty);
            setPropertySelector("block");
        } else {
            console.error('Currently unimplemented.');
        }
        // else if (selectedVisualiation == "googleMap") {
        //     drawGoogleMap(data);
        //     setPropertySelector("none");
        // }
        // else if (selectedVisualiation == "timeLine") {
        //     drawTimeLine(data);
        //     setPropertySelector("none");
        // }
    });
};

// Render the TimeLine Visualisation
function drawTimeLine(classes) {
    console.error('Currently unimplemented.');

    var date = classes[0].dateTime.slice(0, -1);

    var canvasElement = getClearedCanvas();

    var svg = d3.select(canvasElement).append("svg");

    var width = canvasElement.clientWidth;
    var height = canvasElement.clientHeight;

    svg.attr("width", width).attr("height", height);

    var nested = d3.nest()
        .key(function (d) { return d.dateTime; })
        .entries(classes);

    var x = d3.scaleTime()
        .domain([parse(classes[0].dateTime.slice(0, -1)),
        parse(classes[classes.length - 1].dateTime.slice(0, -1))])
        .range([0, width - 200]);

    var y = d3.scaleLinear()
        .rangeRound([0, height-200])
        .domain([0, d3.max(nested, function (d) { return d.values.length; })]);

    var yscale = d3.scaleLinear()
        .rangeRound([height-200, 0])
        .domain([0, d3.max(nested, function (d) { return d.values.length; })]);

    //console.log(d3.max(nested, function (d) { return d.values.length; }) );

    var axisX = d3.axisBottom(x);//.ticks(d3.timeMinute.every(2));
    var axisY = d3.axisLeft(yscale).tickArguments([3, "s"]);

    svg.append("g")
        .attr("transform", "translate(100," + height / 1.15 + ")")
        .call(axisX);

    svg.append("g")
        .attr("transform", "translate(95," + (height - (height / 1.15) - ((100/1.15) - 115)) + ")")
        .call(axisY);

    svg.selectAll(".bar")
        .data(nested)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", function (d) { return x(parse(d.key.slice(0, -1))) + 98; })
        .attr("y", function (d) { return (height / 1.15) - y(d.values.length); })
        .attr("width", 4)
        .attr("height", function (d) { return y(d.values.length); })
        .attr("fill", "blue");

    svg.selectAll(".bar")
        .append("title")
        .text(function (d) {

            var t1 = "File Count : " + d.values.length;

            d.values.forEach(function (element) {
                t1 += "\n" + " - - - - -" + "\n";
                t1 += "Filename: " + element.filename + "\n" +
                    "Filesize: " + element.size + " Byte \n" +
                    "IpAddress: " + element.ipAddress + "\n" +
                    "Datetime:" + parse(element.dateTime.slice(0, -1)) + "\n";
            });
            return t1;

        });
}

// Render The google Map Visualisation
function drawGoogleMap(classes) {
    console.error('Currently unimplemented.');

    var canvasElement = getClearedCanvas();

    // create Map
    var map = new google.maps.Map(canvasElement, {
        zoom: 8,
        center: new google.maps.LatLng(53.574, 9.9747),
        mapTypeId: google.maps.MapTypeId.TERRAIN
    });

    var cords = getAllLatLon(classes);
    console.log(cords);

    cords.forEach(function (element) {
        var marker = new google.maps.Marker({
            position: new google.maps.LatLng(element.lat, element.lon),
            map: map,
            title: "Data Count: " + element.count
        })
    });
}

function extractRelevantData(data) {
    // data contains a full database dump.
    // Of this data, only the current data (no history) is of interest.
    let keys = Object.keys(data);
    let result = []

    keys.forEach(function(key) {
        const data_entry = data[key];

        // data is only relevant if the key is
        // currently available in the database.
        if (data_entry.current == null) {
            return;
        }

        const entry = {
            key: key,
            timestamp: data_entry.current.timestamp,
            size: data_entry.current.size,
            ip: data_entry.current.ip,
            headers: data_entry.current.headers
        };

        result.push(entry);
    });

    return result;
}

// render Treemap
function renderTreemap(classes, property) {
    // Fixup data: Convert full database dump into
    // appropriate format.
    classes = extractRelevantData(classes);

    // ugly Code
    var canvasElement = getClearedCanvas();

    var svg = d3.select(canvasElement).append("svg");

    var width = canvasElement.clientWidth;
    var height = canvasElement.clientHeight;

    // transition time eine s
    var transitionDuration = 1000;

    svg.attr("width", width).attr("height", height);

    // ->
    var color = d3.scaleOrdinal(d3.schemeCategory10);

    var radiusScale = d3.scaleSqrt()
        .domain([d3.min(classes, function (d) { return d.size; }), d3.max(classes, function (d) { return d.size; })])
        .range([10, 100]);

    /*  JR Comment:
        Created nested data structure that maps property -> [object]
     */
    var nested = d3.nest()
        .key(function (d) { return d[property]; })
        .entries(classes);

    console.log(nested);

    // create a root Node for the Tree Structure
    var root = { key: property, children: [] };

    // create Parent Elements for each Nested Attribute
    nested.forEach(function (element) {
        root.children.push({ key: element.key, children: element.values });
    });

    // creating the hierarchy structure for the TreeMap
    var test = d3.hierarchy(root)
        .eachBefore(function (d) { d.data.key = d.data.key; })
        .sum(function (d) { return radiusScale(d.size); })
        .sort(function (a, b) { return b.size - a.size; });

    var treemap = d3.treemap()
        .size([width, height])
        .round(true)
        .paddingInner(2)
        .paddingOuter(2)
        .paddingTop(20);

    treemap(test);

    // Appending all Tree Descenmdants to the svg
    var cell = svg.selectAll(".node")
        .data(test.descendants())
        .enter()
        .append("g")
        .attr("transform", function (d) { return "translate(" + d.x0 + "," + d.y0 + ")"; })
        .attr("class", "node")
        .each(function (d) { d.node = this; })

    // Appending rectangles for all Tree Members
    cell.append("rect")
        .attr("id", function (d) { return d.data.id; })
        .attr("width", function (d) { return (d.x1 - d.x0); })
        .attr("height", function (d) { return (d.y1 - d.y0); })
        .attr("fill", function (d) {

            if (d.parent)
                return color(d.parent.data.key);
            else
                return color("root");
        });


    // Differ leafes vs tree in Visualization
    var leafes = cell.filter(function (d) { return !d.children; })
    var tree = cell.filter(function (d) { return d.children; })

    // set OnClick for leafes
    leafes.on("click", function (d) { setInspector(d.data); })

    // Info for leafes : actual files
    leafes.append("title")
        .text(function (d) {
            return "Key : " + d.data.key + "\n" +
                "Size : " + d.data.size + "Byte" + "\n" +
                "IP : " + d.data.ip + "\n" +
                "DateTime : " + d.data.timestamp + "\n"
            });

    leafes.append("text")
        .attr("x", function (d) { return (d.x1 - d.x0) / 2; })
        .attr("y", function (d) { return (d.y1 - d.y0) / 2; })
        .attr("class", "label")
        .text(function (d) {
            var t = "Key: " + d.data.key;

            if (getTextWidth(t, "bold 12pt arial") > (d.x1 - d.x0))
                return "X";
            else
                return t;
        });

    leafes.append("text")
        .attr("x", function (d) { return (d.x1 - d.x0) / 2; })
        .attr("y", function (d) { return ((d.y1 - d.y0) / 2) + 16; })
        .attr("class", "label")
        .text(function (d) {
            var t = "Size : " + (d.data.size / 1024).toFixed(2) + " KB";

            if (getTextWidth(t, "bold 12pt arial") > (d.x1 - d.x0))
                return "";
            else
                return t;
        });


    // Info for the Tree : nested Property
    tree.append("text")
        .attr("dx", function (d) { return 0; })
        .attr("dy", function (d) { return 15; })
        .text(function (d) {
            return "Key: " + d.data.key;
        });
}

function getClearedCanvas()
{
    var canvasElement = document.getElementById("FileEntryChart");
    removeChildren(canvasElement)

    return canvasElement
}

function removeChildren(node) {
    while (node.hasChildNodes()) {
        node.removeChild(node.firstChild)
    }
}

function removeElementFromArray(array, elem) {
    var index = array.indexOf(elem)
    if (index > -1) {
        array.splice(index, 1)
    }
}

// set the propertys to select from
function setSelectorFields(keys) {
    // Clear existing selectors
    removeChildren(visualSelector);
    removeChildren(propertySelector);

    keys = [
        'key',
        'ip',
        'size',
        'timestamp',
        'headers'
    ];

    keys.forEach(function (element) {
        var optK = document.createElement("option")
        optK.value = element;
        optK.innerHTML = element;

        propertySelector.appendChild(optK);
    });

    // Add new visual options
    visualSelectionOptions = [
        {
            'value': 'treeMap',
            'description': 'Tree Map'
        },
        // {
        //     'value': 'googleMap',
        //     'description': 'IP Google Map'
        // },
        // {
        //     'value': 'timeLine',
        //     'description': 'Time Line'
        // }
    ];

    visualSelectionOptions.forEach(function (element) {
        var optV = document.createElement('option');

        optV.value = element.value;
        optV.innerHTML = element.description;

        visualSelector.appendChild(optV);
    });
}

// get Textwidth of an Element
function getTextWidth(text, font) {
    // if given, use cached canvas for better performance
    // else, create new canvas
    var canvas = getTextWidth.canvas || (getTextWidth.canvas = document.createElement("canvas"));
    var context = canvas.getContext("2d");
    context.font = font;
    var metrics = context.measureText(text);
    return metrics.width;
};

// Set Data to display for a selected FileEntry
function setInspector(data) {
    removeChildren(headerl)

    idp.innerText = "Key : " + data.key;
//    filenamep.innerText = "Filename : " + data.filename;
    sizep.innerText = "Size : " + data.size + " Byte";
    ipp.innerText = "IP : " + data.ip;
    datep.innerText = "Date : " + data.timestamp;
    // countryp.innerText = "Country : " + data.country;
    // regionNamep.innerText = "Region Name : " + data.regionName;
    // cityp.innerText = "City : " + data.city;
    // latp.innerText = "Lat : " + data.lat;
    // lonp.innerText = "Lon : " + data.lon;
    // ispp.innerText = "ISP : " + data.isp;

    const headers = data.headers;

    headers.forEach(function (header) {
        const text = header.key + " = " + header.value;

        var entry = document.createElement('li');
        entry.appendChild(document.createTextNode(text));

        headerl.appendChild(entry);
    });
};

// reset the Inspector for reuse
function resetInspector() {
    removeChildren(headerl)

    idp.innerText = "Key : ";
//    filenamep.innerText = "Filename : ";
    sizep.innerText = "Size : ";
    ipp.innerText = "IP : ";
    datep.innerText = "Date : ";
    // countryp.innerText = "Country : ";
    // regionNamep.innerText = "Region Name : ";
    // cityp.innerText = "City : ";
    // latp.innerText = "Lat : ";
    // lonp.innerText = "Lon : ";
    // ispp.innerText = "ISP : ";
};

// get Lat Lon for grouping
function getAllLatLon(classes) {

    var nested = d3.nest()
        .key(function (d) { return d["ipAddress"]; })
        .entries(classes);

    var ret = [];

    nested.forEach(function (element) {
        ret.push({ lat: element.values[0].lat, lon: element.values[0].lon, count: element.values.length });
    });

    return ret;
}