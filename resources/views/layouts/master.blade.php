<!DOCTYPE html>
<html lang="en">

    <head>
        <meta charset="utf-8">
        <title>MBJ Indonesia - Ayo Kerja di Jepang</title>
        <meta content="width=device-width, initial-scale=1.0" name="viewport">
        <meta content="LPK Tangerang, LPK terpercaya, LPK jepang, LPK Matahari Bulan Jepang Indonesia, LPK MBJ Indonesia, LPK Jepang terpercaya" name="keywords">
        <meta content="LPK Matahari Bulan Jepang Indonesia (MBJ) adalah lembaga pelatihan kerja terpercaya di Tangerang yang memfokuskan pada pelatihan dan penempatan kerja ke Jepang. Dengan pengalaman dan dedikasi tinggi, kami siap membantu mewujudkan impian Anda bekerja di Jepang." name="description">

        <!-- Google Web Fonts -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&family=Poppins:wght@200;300;400;500;600&display=swap" rel="stylesheet">
        <link rel="icon" type="image/svg+xml" href="{{ asset('mbj-logo.ico') }}" />
        <link rel="preload" fetchpriority="high" as="image" href="{{ asset('asset/img/home-1.jpeg') }}" type="image/jpeg">


        {{-- Include Styles --}}
        @include('panels/styles')
    </head>

    <body>

        <!-- Spinner Start -->
        <div id="spinner" class="show bg-white position-fixed translate-middle w-100 vh-100 top-50 start-50 d-flex align-items-center justify-content-center">
            <div class="spinner-border text-secondary" style="width: 3rem; height: 3rem;" role="status">
                <span class="sr-only">Loading...</span>
            </div>
        </div>
        <!-- Spinner End -->


        @include('layouts/navbar')


        @yield('content')

        @include('layouts/footer')

        @include('components/chat-widget')


        <!-- Back to Top -->
        <a href="#" class="btn btn-primary btn-lg-square back-to-top"><i class="fa fa-arrow-up"></i></a>   

    @include('panels/scripts')
    </body>

</html>