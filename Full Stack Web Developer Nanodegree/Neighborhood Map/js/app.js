var infoWindow, map;
var ViewModel;

// Display Message Box. 
// It is more convenient to use jQuery to display a div box. Besides this is more like View rather than ViewModel... 
var msgbox = (function(msgtext) {
	$("#msgtext").html(msgtext);
	$("#msgbox").delay(200).fadeIn().delay(3000).fadeOut();
	$("#msgbox").click(function(){$("#msgbox").fadeOut(500)});
});

// Create a map variable
function initMap() {

		map = new google.maps.Map(document.getElementById('map'), {
			center: initialCenter,
			zoom: 10
		});
		map.fitBounds(initialBound);// fit map bounds according to data. use getBounds() after loads. 
		
		// Center Map button
		var centerControlDiv = document.createElement('div');
		var centerControl = new CenterControl(centerControlDiv, map);
		centerControlDiv.index = 1;
		map.controls[google.maps.ControlPosition.TOP_CENTER].push(centerControlDiv);
		
		// Load ViewModel after map loads. 
		ViewModel = new locationModel(initialLocations);
		ko.applyBindings(ViewModel);

};


function locationModel(locations) {
	var self = this;
	var url; // API request url.
	self.locationList = ko.observableArray(locations);  // create to observableArray from initial data. 
	self.infowindow = new google.maps.InfoWindow();
	self.filter = ko.observable("");

// FourSquare API constants. 
	var fsqClientID = '[REPLACE WITH YOUR SECRET]';
	var fsqClientSecret = '[REPLACE WITH YOUR SECRET]';
		
		
	var fsqRequestURLBase =	'https://api.foursquare.com/v2/venues/';
	var fsqRequestAuth = 'v=20180223&client_id=' + fsqClientID + '&client_secret=' + fsqClientSecret;

// load info from APIs for each marker, and add markers in ViewModel
	self.locationList().forEach(function(oneLocation,locationIndex){
		let position = oneLocation.position;
		let title = oneLocation.name;
		oneLocation.marker = new google.maps.Marker({
			position: position,
			title: title,
			map: map, 
			animation: google.maps.Animation.Drop
				  //todo: timeout Drop
		});
		// FourSquare info from API. 
		oneLocation.fsdata={};
		
		if(fsqClientSecret=='[REPLACE WITH YOUR SECRET]'){ 
			// using foursquare explorer token for testing
			// https://foursquare.com/developers/explore
			// may expire any time 
			// Please DO NOT use this token for live applications in production, according to Foursquare Document.
			url='https://api.foursquare.com/v2/venues/search?ll='+ position.lat + ',' + position.lng + '&oauth_token=KJ0U4UDC1LJUC2BNYJRTCXPIPELSKDAI5IHXTXDJVOGJSRIS&v=20180223&query='+ encodeURIComponent(title);
		} else {
			url = fsqRequestURLBase+ 'search?'+ fsqRequestAuth + "&ll=" + position.lat + ',' + position.lng + "&query=" + encodeURIComponent(title);
		};
		$.ajax({
			url: url,
			timeout: 10000,
			dataType: 'json', 
			success: function(data){
				let fsResponse
				if(data.response.venues[0]){
					fsResponse = data.response.venues[0];
					oneLocation.fsdata.fsid = fsResponse.id;
					oneLocation.fsdata.fsname = fsResponse.name;
					oneLocation.fsdata.stats = fsResponse.stats;
					if(typeof fsResponse.menu != 'undefined'){
						oneLocation.fsdata.menu = fsResponse.menu
					};
				} else{
					console.log("Foursquare API returns nothing.");
					// msgbox("Foursquare API returns nothing."); // Users may not care about "nothing"
				}
			},
			error: function(data){
				console.log("Foursquare API Error: ",data);
				msgbox("Foursquare API Error code " + data.status+": "+ data.statusText);
			}
		});
		
		// Google Maps PlacesService. More accurate than foursquare? 
		var geocoder = new google.maps.Geocoder;
		var placeservice = new google.maps.places.PlacesService(map);
		var radarSearchRequest = {location: position, radius: 300, keyword: title};
window.setTimeout( function(){  
		placeservice.radarSearch(radarSearchRequest, function (results, status) {
			console.log(oneLocation,locationIndex, Date());
			if (status === google.maps.places.PlacesServiceStatus.OK) {
				if(results[0]){
					oneLocation.place_id = results[0].place_id;
					window.setTimeout( function(){   //to avoid OVER_QUERY_LIMIT error 
					console.log(results[0].place_id,locationIndex, Date());
					placeservice.getDetails({placeId:oneLocation.place_id}, function (results, status) {
						if (status === google.maps.places.PlacesServiceStatus.OK) {
							if(results){
								oneLocation.formatted_phone_number = results.formatted_phone_number;
								oneLocation.formatted_address = results.formatted_address;
							} else {
								window.alert('No results found');
							}
						} else { // Google Map API Error Handling
							msgbox('Google Maps PlaceService failed:' + status);
						}
					})}, 300*locationIndex);  

				} else { // Google Map API Error Handling
					msgbox('Google Maps PlaceService failed:' + status);
				}
			} else { // Google Map API Error Handling
				msgbox('Google Maps PlaceService failed:' + status);
			}
		});
}, 300*locationIndex); 
		oneLocation.marker.addListener('click', function(){
			self.openInfoWindow(this, self.infowindow, oneLocation)
		});
	}); // end loading single marker info from apis. 

	self.openInfoWindow = function(marker, infowindow, oneLocation){
		let fsid = oneLocation.fsdata.fsid;
		let infoWindowContent = `<div><b>${marker.title}</b><br/>` 
		if (typeof oneLocation.formatted_phone_number !="undefined"){
			infoWindowContent += `Tel: ${oneLocation.formatted_phone_number}`  ;
		};
		if (typeof oneLocation.formatted_address !="undefined"){
			infoWindowContent += `<br />${oneLocation.formatted_address}` ;
		};
		if (typeof oneLocation.fsdata.menu !="undefined"){
			infoWindowContent += `<br/><a  target="_blank" href="${oneLocation.fsdata.menu.url}">Check Menu on Foursquare</a>`;
		};
		
		
		if(fsqClientSecret=='[REPLACE WITH YOUR SECRET]'){ 
			// using foursquare explorer token for testing
			// https://foursquare.com/developers/explore
			// may expire any time 
			// Please DO NOT use this token for live applications in production, according to Foursquare Document.
			url='https://api.foursquare.com/v2/venues/'+fsid+'?&oauth_token=KJ0U4UDC1LJUC2BNYJRTCXPIPELSKDAI5IHXTXDJVOGJSRIS&v=20180223';
		} else {
			url = fsqRequestURLBase + fsid + '?'+ fsqRequestAuth ;
		};
		
		$.ajax({
			url: url,
			timeout: 20000,
			dataType: 'json', 
			success: function(data){
				let fsphotos,fsphotoPrefix,fsphotoSuffix, pickAPic, picurl;

				if(data.response.venue.photos.groups[0].items){
					oneLocation.fsdata.photos = data.response.venue.photos.groups[0].items;
					fsphotos=data.response.venue.photos.groups[0].items;
					
					// randmomly pick a picture 
					pickAPic=Math.ceil(Math.random()*fsphotos.length)-1;
					picurl = fsphotos[pickAPic].prefix + '256x192' + fsphotos[pickAPic].suffix;
					
					// Asynchronously refresh infowindow
					self.infowindow.setContent(infoWindowContent+`<br/><div><a href="https://foursquare.com/v/${fsid}"><img class="center-block img-thumbnail" src="${picurl}" /><br/><span class="pull-right">Photo <img src="./static/Powered-by-Foursquare-full-color-300_preview.png" height="26px"></span></a></div></div>`);
				} else{
					console.log("Foursquare API returns no pic.");
					// msgbox("Foursquare API returns nothing."); // Users may not care about "nothing"
				}
			},
			error: function(data){
				console.log("Foursquare API Error: ",data);
				msgbox("Foursquare API Error code " + data.status+": "+ data.statusText);
			}
		});
		
		self.infowindow.setContent(infoWindowContent+'</div>');
		self.infowindow.open(map, marker);
		self.markerBounce(marker);
	};

	self.markerBounce = (function (marker){
		marker.setAnimation(google.maps.Animation.BOUNCE);
		setTimeout(function(){
			marker.setAnimation(null);
		}, 1420)
	});
	
	// for filter 
	self.visibleLocations = ko.computed(function(){
		let filter = self.filter().toLowerCase();
		if (!filter){
			ko.utils.arrayForEach(self.locationList(), function(oneLocation){
				oneLocation.marker.setVisible(true); 
			});
			return self.locationList();
		} else {
			return ko.utils.arrayFilter(self.locationList(), function(oneLocation) {
				let rst = (oneLocation.name.toLowerCase().search(filter)>=0);
				oneLocation.marker.setVisible(rst);
				return rst;
        })
		};
	});
	
	self.remove = function(oneLocation){
		bootbox.confirm("Deleting <b>" + oneLocation.name +"</b>, are you sure?",function(result){
			if(result){
			oneLocation.marker.setMap(null);
			self.locationList.remove(oneLocation);
			}
		})
	};
	
	self.boundLatLng = ko.computed(function(){
		let l = self.locationList().length;
		let rst={latMin:100.0,latMax:-100.0,lngMin:190.0,lngMax:-190.0,avgCenter:{lat:0,lng:0}, boundMin:{lat:0,lng:0},boundMax:{lat:0,lng:0}};
		for (let i = 0; l>i; i++){
			if (self.locationList()[i].position.lat < rst.latMin ){
				rst.latMin=self.locationList()[i].position.lat;
			}
			if (self.locationList()[i].position.lat > rst.latMax ){
				rst.latMax=self.locationList()[i].position.lat;
			}
			if (self.locationList()[i].position.lng < rst.lngMin ){
				rst.lngMin=self.locationList()[i].position.lng;
			}
			if (self.locationList()[i].position.lng > rst.lngMax ){
				rst.lngMax=self.locationList()[i].position.lng;
			}
		};
		rst.avgCenter={lat: (rst.latMin+rst.latMax)/2,lng: (rst.lngMin+rst.lngMax)/2};
		rst.boundMax.lat = rst.latMax;
		rst.boundMax.lng = rst.lngMax;
		rst.boundMin.lat = rst.latMin;
		rst.boundMin.lng = rst.lngMin;
		return rst;
	});

	
};

function CenterControl(controlDiv, map) {

  // Set CSS for the control border.
  var controlUI = document.createElement('div');
  controlUI.style.backgroundColor = '#fff';
  controlUI.style.border = '2px solid #fff';
  controlUI.style.borderRadius = '3px';
  controlUI.style.boxShadow = '0 2px 6px rgba(0,0,0,.3)';
  controlUI.style.cursor = 'pointer';
  controlUI.style.marginBottom = '22px';
  controlUI.style.textAlign = 'center';
  controlUI.title = 'Click to recenter the map';
  controlDiv.appendChild(controlUI);

  // Set CSS for the control interior.
  var controlText = document.createElement('div');
  controlText.style.color = 'rgb(25,25,25)';
  controlText.style.fontFamily = 'Roboto,Arial,sans-serif';
  controlText.style.fontSize = '16px';
  controlText.style.lineHeight = '38px';
  controlText.style.paddingLeft = '5px';
  controlText.style.paddingRight = '5px';
  controlText.innerHTML = 'Center Map';
  controlUI.appendChild(controlText);

  // Setup the click event listeners: simply set the map to Chicago.
  controlUI.addEventListener('click', function() {
		map.setCenter(ViewModel.boundLatLng().avgCenter);
		map.fitBounds(getBounds(ViewModel.boundLatLng().boundMax, ViewModel.boundLatLng().boundMin));
//		drop(50);
  });

};


function getBounds(boundsMin, boundsMax){
	var bounds = new google.maps.LatLngBounds();
//	var latLngMin = new google.maps.LatLng(ViewModel.boundLatLng().latMin, ViewModel.boundLatLng().lngMin);
//	var latLngMax = new google.maps.LatLng(ViewModel.boundLatLng().latMax, ViewModel.boundLatLng().lngMax);
	bounds.extend(boundsMin);
	bounds.extend(boundsMax);
	return bounds
}

// ****** Older (and ugly) version of error handling:
// ****** check if there is a google object after 10s onload. 
// // check if google map api js load successfully.
// function checkGoogleLoad(){
// window.setTimeout(function(){
// 	if(typeof google === "undefined"){
// 		alert("Can not load Google Maps, check network connection?")
// 	}
// }, 10000)
// };

// ****** 2018/02/25 new error handling. 
function mapErrorHandler(){
		alert("Error loading Google Maps. Check network connection?")
};

// TODO: flickr API
// https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=[   ]&lat=34.038343&lon=-118.261817&per_page=5&page=1&format=json