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
              <img class="img-fluid" src="{{ asset('asset/img/company.png') }}" alt="">
            </div>
          </div>
          <div class="col-lg-6">
            <div class="h_blog_text">
              <div class="h_blog_text_inner left right">
                <h4>Selamat Datang di LPK MBJ Indonesia</h4>
                <p>
                  LPK Matahari Bulan Jepang Indonesia merupakan Lembaga pendidikan Bahasa Jepang dan pelatihan kerja untuk mempersiapkan tenaga kerja yang handal khususnya ke Jepang.
                </p>
                <p>
                  LPK Matahari Bulan Jepang Indonesia didirikan sejak  20 Mei 2023 dan telah mendapatkan izin usaha dari kementerian ketenagakerjaan RI di tahun 2023
                </p>
                <p>
                  Dengan semangat untuk mengurangi angka pengangguran di Indonesia dan demi membantu kebutuhan Negara Jepang dalam memenuhi jumlah tenaga kerjanya, kami tidak ingin melewatkan kesempatan untuk  mewadahi supply dan demand yang dibutuhkan oleh kedua negara tersebut
                </p>
                <p>
                  Pendidikan dan pelatihan utama yang kami berikan adalah bahasa dan budaya. Karena bagi kami bekerja atau sekolah ke Jepang bukanlah untuk pergi berwisata semata, melainkan untuk mengejar tujuan baru yang harus dicapai. Kami percaya jika pembentukan karakter dapat dibangun secara terus menerus, maka kami mampu mengirimkan siswa yang memiliki kemampuan, keterampilan, kemandirian dan kedisiplinan yang tinggi. Dan setelah mereka kembali ke Indonesia, mereka  akan menjadi generasi baru yang dapat membangun Indonesia menjadi lebih baik lagi
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
                Menjadikan LPK Matahari Bulan Jepang Indonesia sebagai lembaga pendidikan yang professional, dan berkualitas yang dapat menghasilkan sumber daya manusia yang mampu berkompetisi di era global yang memaknai tantangan peluang sesuai dengan perkembangan ilmu pengetahuan dan teknologi untuk memenuhi kebutuhan masyarakat melalui pengembangan pembelajaran bahasa asing.
              </p>
            </div>
          </div>
        </div>

        <div class="col-lg-6 col-md-6 col-sm-12">
          <div class="single_feature">
            <div class="icon"><span class="flaticon-book"></span></div>
            <div class="desc">
              <h4 class="mt-3 mb-2">Misi</h4>
              <ul>
                <li>
                  <p>Menyelenggarakan program pendidikan dan pelatihan bahasa jepang secara profesional.</p>
                </li>
                <li>
                  <p>Mengadakan kegiatan pengabdian kepada masyarakat secara edukatif, konsisten, dan terprogram dengan mengacu kepada pengembangan bahasa asing.</p>
                </li>
                <li>
                  <p>Mendidik generasi muda agar memiliki semangat kerja yang tinggi, disiplin dan mandiri.</p>
                </li>
                <li>
                  <p>Meningkatkan hubungan kerja sama bidang tenaga kerja antara indonesia dengan jepang.</p>
                </li>
              </ul>
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
                  {{-- <h6>Head Office</h6> --}}
                  <h6>Branch Office</h6>
                  <p>
                    Jl. Kh. Moh. Kup No.24, RT.005/RW.001, Pinang, Kec. Pinang, Kota Tangerang, Banten 15145
                    {{-- Jl. Taman Buah Boulevard No.003 Puribeta, RT.004/RW.2, Larangan Utara, Kec. Larangan, Kota Tangerang, Banten 15154 --}}
                  </p>
                </div>
              </div>
            </div>
            <div class="col-lg-6">
                <div class="h_blog_maps">
                  <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2121.1081457436617!2d106.68759010820143!3d-6.217300227862818!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e69f90034ecac1f%3A0x7588ad81209d4f03!2sLPK%20MATAHARI%20BULAN%20JEPANG%20INDONESIA!5e0!3m2!1sid!2sid!4v1736708222323!5m2!1sid!2sid" width="650" height="433" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
                    {{-- <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d495.7784891288964!2d106.72222011026852!3d-6.233658524462916!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2e69fa09d1d75bcf%3A0xa0c16a498c397606!2sPuri%20Beta%202%20Taman%20Buah!5e0!3m2!1sid!2sid!4v1723369381374!5m2!1sid!2sid" 
                        width="100%" height="430" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade">
                    </iframe> --}}
                </div>
            </div>
            
          </div>
        
    </div>
</div>
<!-- Training End -->
    

<!-- About End -->

@endsection

