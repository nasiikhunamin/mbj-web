@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Kegiatan Kami</h3>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item active text-secondary">Galeri</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- Gallery Start -->
<div class="container-fluid py-5">
    <div class="container">
        <div class="text-center mx-auto mb-5" style="max-width: 700px;">
            <h2 class="display-7 mb-4">Dokumentasi Kegiatan LPK Matahari Bulan</h2>
        </div>

        <div class="row g-4">
            <!-- Gallery Item 1 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.1s">
                <div class="card gallery-item h-100">
                    <img src="{{asset('asset/img/galery-1.jpeg')}}" class="card-img-top" alt="Kegiatan 1">
                    <div class="card-body">
                        <h5 class="card-title">Pelatihan Bahasa Jepang</h5>
                        <p class="card-text">Kegiatan belajar mengajar bahasa Jepang dengan metode yang interaktif dan menyenangkan.</p>
                    </div>
                </div>
            </div>

            <!-- Gallery Item 2 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.3s">
                <div class="card gallery-item h-100">
                    <img src="{{asset('asset/img/galery-2.jpeg')}}" class="card-img-top" alt="Kegiatan 2">
                    <div class="card-body">
                        <h5 class="card-title">Pelatihan Bahasa Jepang</h5>
                        <p class="card-text">Kegiatan belajar mengajar bahasa Jepang dengan metode yang interaktif dan menyenangkan.</p>
                    </div>
                </div>
            </div>

            <!-- Gallery Item 3 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.5s">
                <div class="card gallery-item h-100">
                    <img src="{{asset('asset/img/galery-3.jpeg')}}" class="card-img-top" alt="Kegiatan 3">
                    <div class="card-body">
                        <h5 class="card-title">Pelatihan Bahasa Jepang</h5>
                        <p class="card-text">Kegiatan belajar mengajar bahasa Jepang dengan metode yang interaktif dan menyenangkan.</p>
                    </div>
                </div>
            </div>

            <!-- Gallery Item 4 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.1s">
                <div class="card gallery-item h-100">
                    <img src="{{asset('asset/img/galery-4.jpeg')}}" class="card-img-top" alt="Kegiatan 4">
                    <div class="card-body">
                        <h5 class="card-title">Pelatihan Bahasa Jepang</h5>
                        <p class="card-text">Kegiatan belajar mengajar bahasa Jepang dengan metode yang interaktif dan menyenangkan.</p>
                    </div>
                </div>
            </div>

            <!-- Gallery Item 5 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.3s">
                <div class="card gallery-item h-100">
                    <img src="{{asset('asset/img/galery-5.jpeg')}}" class="card-img-top" alt="Kegiatan 5">
                    <div class="card-body">
                        <h5 class="card-title">Pelatihan Bahasa Jepang</h5>
                        <p class="card-text">Kegiatan belajar mengajar bahasa Jepang dengan metode yang interaktif dan menyenangkan.</p>
                    </div>
                </div>
            </div>

            <!-- Gallery Item 6 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.5s">
                <div class="card gallery-item h-100">
                    <img src="{{asset('asset/img/galery-6.jpeg')}}" class="card-img-top" alt="Kegiatan 6">
                    <div class="card-body">
                        <h5 class="card-title">Pelatihan Bahasa Jepang</h5>
                        <p class="card-text">Kegiatan belajar mengajar bahasa Jepang dengan metode yang interaktif dan menyenangkan.</p>
                    </div>
                </div>
            </div>

            <!-- Gallery Item 7 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.1s">
                <div class="card gallery-item h-100">
                    <img src="{{asset('asset/img/galery-7.jpeg')}}" class="card-img-top" alt="Kegiatan 7">
                    <div class="card-body">
                        <h5 class="card-title">Pelatihan Bahasa Jepang</h5>
                        <p class="card-text">Kegiatan belajar mengajar bahasa Jepang dengan metode yang interaktif dan menyenangkan.</p>
                    </div>
                </div>
            </div>

            <!-- Gallery Item 8 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.3s">
                <div class="card gallery-item h-100">
                    <img src="{{asset('asset/img/galery-8.jpeg')}}" class="card-img-top" alt="Kegiatan 8">
                    <div class="card-body">
                        <h5 class="card-title">Pelatihan Bahasa Jepang</h5>
                        <p class="card-text">Kegiatan belajar mengajar bahasa Jepang dengan metode yang interaktif dan menyenangkan.</p>
                    </div>
                </div>
            </div>

            <!-- Gallery Item 9 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.5s">
                <div class="card gallery-item h-100">
                    <img src="{{asset('asset/img/galery-9.jpeg')}}" class="card-img-top" alt="Kegiatan 9">
                    <div class="card-body">
                        <h5 class="card-title">Pelatihan Bahasa Jepang</h5>
                        <p class="card-text">Kegiatan belajar mengajar bahasa Jepang dengan metode yang interaktif dan menyenangkan.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<!-- Gallery End -->

<style>
.gallery-item {
    transition: transform 0.3s ease;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.gallery-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

.gallery-item img {
    object-fit: cover;
    height: 250px;
}

.card-body {
    background: #fff;
}
</style>

@endsection