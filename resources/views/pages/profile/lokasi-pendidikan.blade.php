@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Lokasi Pendidikan</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Profile</a></li>
            <li class="breadcrumb-item active text-secondary">Lokasi Pendidikan</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- Training Start -->
<div class="container-fluid training overflow-hidden bg-light py-5">
    <div class="container py-5">
        <div class="row h_blog_item">
            <div class="col-lg-6">
              <div class="h_blog_text">
                <div class="h_blog_text_inner left right">
                    <h4>Kunjungi Kami</h4>
                    <h6>Head Office</h6>
                    <p>
                        Jl. Taman Buah Boulevard No.003 Puribeta, RT.004/RW.2, Larangan Utara, Kec. Larangan, Kota Tangerang, Banten 15154
                    </p>
                    <h6>Head Office</h6>
                    <p>
                        Jl. Taman Buah Boulevard No.003 Puribeta, RT.004/RW.2, Larangan Utara, Kec. Larangan, Kota Tangerang, Banten 15154
                    </p>
                </div>
              </div>
            </div>
            <div class="col-lg-6">
                <div class="h_blog_maps">
                    <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d495.7784891288964!2d106.72222011026852!3d-6.233658524462916!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e69fa09d1d75bcf%3A0xa0c16a498c397606!2sPuri%20Beta%202%20Taman%20Buah!5e0!3m2!1sid!2sid!4v1723369381374!5m2!1sid!2sid" 
                        width="100%" height="430" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade">
                    </iframe>
                </div>
            </div>
        </div>
        <div class="row g-4 py-5">
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.5s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-3.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Kelas Kami</h5>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.7s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-4.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Fasilitas Kelas</h5>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.5s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-3.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Fasilitas Kelas</h5>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.7s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/team-4.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Fasilitas Kelas</h5>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<!-- Training End -->

@endsection

