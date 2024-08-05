document.querySelectorAll('.sort-buttons button').forEach(button => {
    button.addEventListener('click', function() {
        // 모든 버튼에서 'active' 클래스 제거
        document.querySelectorAll('.sort-buttons button').forEach(btn => btn.classList.remove('active'));
        
        // 클릭된 버튼에 'active' 클래스 추가
        this.classList.add('active');
        
        // 선택한 정렬 기준에 따라 페이지를 새로 로드
        let sortCriteria = this.classList.contains('sort-left') ? 'distance' : 'reviews';
        let currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set('sort', sortCriteria); // 'sort' 파라미터를 설정
        window.location.href = currentUrl.href; // 페이지를 새로 로드
    });
});
