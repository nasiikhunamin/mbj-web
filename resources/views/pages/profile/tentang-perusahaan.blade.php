@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Tentang Perusahaan</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Profile</a></li>
            <li class="breadcrumb-item active text-secondary">Tentang Perusahaan</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- About Start -->
<div class="container-fluid overflow-hidden py-5">
    <div class="container">
        <div class="row h_blog_item">
          <div class="col-lg-6">
            <div class="h_blog_img">
              <img class="img-fluid" src="{{ asset('asset/img/about.png') }}" alt="">
            </div>
          </div>
          <div class="col-lg-6">
            <div class="h_blog_text">
              <div class="h_blog_text_inner left right">
                <h4>Welcome to our Institute</h4>
                <p>
                  Subdue whales void god which living don't midst lesser
                  yielding over lights whose. Cattle greater brought sixth fly
                  den dry good tree isn't seed stars were.
                </p>
                <p>
                  Subdue whales void god which living don't midst lesser yieldi
                  over lights whose. Cattle greater brought sixth fly den dry
                  good tree isn't seed stars were the boring.
                </p>
              </div>
            </div>
          </div>
        </div>
    </div>
</div>
<section class="feature_area section_gap_top title-bg">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-lg-5">
          <div class="main_title">
            <h2 class="mb-3 text-white">Visi dan Misi Kami</h2>
            <p>
              Ini adalah visi misi kami
            </p>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col-lg-6 col-md-6 col-sm-12">
          <div class="single_feature">
            <div class="icon"><span class="flaticon-student"></span></div>
            <div class="desc">
              <h4 class="mt-3 mb-2">Visi</h4>
              <p>
                Dimulai dengan tekad untuk membawa dampak perubahan kualitas yang besar kepada generasi muda Indonesia dan kepercayaan bahwa pendidikan merupakan satu-satunya jalan terbaik untuk mencapainya maka didirikanlah Purwadhika pada tahun 1987.
              </p>
              <p>
                Oleh karenanya Purwadhika bukan hanya sekedar sebagai sekolah melainkan sebagai institusi pembawa perubahan kehidupan yang.
              </p>
            </div>
          </div>
        </div>

        <div class="col-lg-6 col-md-6 col-sm-12">
          <div class="single_feature">
            <div class="icon"><span class="flaticon-book"></span></div>
            <div class="desc">
              <h4 class="mt-3 mb-2">Misi</h4>
              <p>
                Merancang program yang bukan hanya untuk meningkatkan kemampuan atau keahlian para siswa tetapi untuk mempersiapkan mereka agar dapat berkontribusi sebagai profesional handal di dunia industri masa kini dan masa depan.
              </p>
              <p>
                Menyediakan tenaga pengajar yang berprestasi di bidang akademis dan berpengalaman secara profesional di industri masa kini.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
</section>

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
        
    </div>
</div>
<!-- Training End -->
    

<!-- About End -->

@endsection

