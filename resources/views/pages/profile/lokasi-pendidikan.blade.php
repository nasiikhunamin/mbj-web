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
                    <h4>Kunjungi Head Office Kami</h4>
                    <p>
                        Jl. Taman Buah Boulevard No.003 Puribeta, RT.004/RW.2, Larangan Utara, Kec. Larangan, Kota Tangerang, Banten 15154
                    </p>
                </div>
              </div>
            </div>
            <div class="col-lg-6">
                <div class="h_blog_maps">
                    <iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d991.556979249192!2d106.72222!3d-6.233658!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e69fb0078016aaf%3A0x7d15aaef50c8931a!2sLPK%20Matahari%20Bulan%20Jepang%20Indonesia!5e0!3m2!1sid!2sid!4v1736708807011!5m2!1sid!2sid" width="650" height="405" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="h_blog_text">
                  <div class="h_blog_text_inner left right">
                      <h4>Kunjungi Branch Office Kami</h4>   
                      <p>
                        Jl. Kh. Moh. Kup No.24, RT.005/RW.001, Pinang, Kec. Pinang, Kota Tangerang, Banten 15145
                      </p>
                  </div>
                </div>
              </div>
              <div class="col-lg-6">
                  <div class="h_blog_maps">
                    <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2121.1081457436617!2d106.68759010820143!3d-6.217300227862818!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e69f90034ecac1f%3A0x7588ad81209d4f03!2sLPK%20MATAHARI%20BULAN%20JEPANG%20INDONESIA!5e0!3m2!1sid!2sid!4v1736708703829!5m2!1sid!2sid" width="650" height="405" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
                  </div>
              </div>
        </div>
        {{-- <div class="row g-4 py-5">
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.5s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/class1.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Ruang Kelas 1</h5>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.7s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/class2.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Ruang Kelas 2</h5>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.5s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/facility1.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Asrama Putra</h5>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.7s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/facility2.jpg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Asrama Putri</h5>
                    </div>
                </div>
            </div>
        </div> --}}
    </div>
</div>
<!-- Training End -->

@endsection

