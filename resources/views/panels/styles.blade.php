<!-- Preload Font Awesome and Bootstrap Icons CSS -->
<link rel="preload" href="https://use.fontawesome.com/releases/v5.15.4/css/all.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.15.4/css/all.css"></noscript>
<link rel="preload" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.4.1/font/bootstrap-icons.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.4.1/font/bootstrap-icons.css"></noscript>

<!-- Preload Libraries CSS -->
<link rel="preload" href="{{ asset('asset/vendors/animate/animate.min.css') }}" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{{ asset('asset/vendors/animate/animate.min.css') }}"></noscript>
<link rel="preload" href="{{ asset('asset/vendors/owlcarousel/assets/owl.carousel.min.css') }}" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{{ asset('asset/vendors/owlcarousel/assets/owl.carousel.min.css') }}"></noscript>

<!-- Preload Bootstrap CSS -->
<link rel="preload" href="{{ asset('asset/css/bootstrap.min.css') }}" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{{ asset('asset/css/bootstrap.min.css') }}"></noscript>

<!-- Preload Theme CSS -->
<link rel="preload" href="{{ asset('asset/css/style.css?v=1.1') }}" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{{ asset('asset/css/style.css?v=1.1') }}"></noscript>

{{-- Page Styles --}}
@yield('page-style')
