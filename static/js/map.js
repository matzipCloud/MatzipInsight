function initMap() {
    var mapOptions = {
        center: new naver.maps.LatLng(37.5665, 126.9780),
        zoom: 10,
        mapTypeControl: true
    };

    var map = new naver.maps.Map('map', mapOptions);

    var markers = [];
    var bounds = new naver.maps.LatLngBounds();

    mapData.forEach(function(result) {
        var markerPosition = new naver.maps.LatLng(result.latitude, result.longitude);
        var marker = new naver.maps.Marker({
            position: markerPosition,
            map: map,
            title: result.Name,
            icon: {
                content: '<div class="custom-pin">' + result.Name + '</div>',
                anchor: new naver.maps.Point(15, 15)
            }
        });

        markers.push(marker);
        bounds.extend(markerPosition); // 각 마커의 위치를 bounds에 추가
    });

    if (markers.length > 0) {
        map.fitBounds(bounds); // 모든 마커를 포함하는 영역으로 지도 확대
    }
}

naver.maps.onJSContentLoaded = initMap;
