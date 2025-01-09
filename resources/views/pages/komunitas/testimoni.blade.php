@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Apa Kata Mereka</h3>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item active text-secondary">Testimoni</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<!-- Testimonials Start -->
<div class="container-fluid py-5">
    <div class="container">
        <div class="text-center mx-auto mb-5" style="max-width: 700px;">
            <h2 class="display-7 mb-4">Testimoni Alumni LPK Matahari Bulan Jepang Indonesia</h2>
        </div>
        
        <div class="row g-4">
            <!-- Testimonial Item 1 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.1s">
                <div class="testimonial-item rounded p-4 p-lg-5">
                    <div class="d-flex align-items-center mb-4">
                        <img class="flex-shrink-0 rounded-circle border border-primary" src="{{asset('asset/img/testimoni1.jpg')}}" alt="Profile" style="width: 100px; height: 100px;">
                        <div class="ms-4">
                            <h5 class="mb-1">Susanto</h5>
                            <p class="mb-0 text-primary">Construction Job</p>
                        </div>
                    </div>
                    <p class="mb-0">Fasilitator/instruktur sangat berkompeten. Materi yang disampaikan dapat dicerna dengan sangat baik oleh kami sehingga sesuai dengan apa yang kami hadapi di lapangan dengan materi di program pelatihan ini</p>
                </div>
            </div>

            <!-- Testimonial Item 2 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.3s">
                <div class="testimonial-item rounded p-4 p-lg-5">
                    <div class="d-flex align-items-center mb-4">
                        <img class="flex-shrink-0 rounded-circle border border-primary" src="{{asset('asset/img/testimoni2.jpg')}}" alt="Profile" style="width: 100px; height: 100px;">
                        <div class="ms-4">
                            <h5 class="mb-1">Farhan</h5>
                            <p class="mb-0 text-primary">Electrical Welding</p>
                        </div>
                    </div>
                    <p class="mb-0">Instruktur memiliki pengalaman yang cukup luas sesuai dengan bidangnya. Dan semua fasilitas yang diberikan oleh LPK Matahari Bulan Jepang Indonesia selama pelatihan sudah memuaskan</p>
                </div>
            </div>

            <!-- Testimonial Item 3 -->
            <div class="col-lg-4 col-md-6 wow fadeInUp" data-wow-delay="0.5s">
                <div class="testimonial-item rounded p-4 p-lg-5">
                    <div class="d-flex align-items-center mb-4">
                        <img class="flex-shrink-0 rounded-circle border border-primary" src="{{asset('asset/img/testimoni3.jpg')}}" alt="Profile" style="width: 100px; height: 100px;">
                        <div class="ms-4">
                            <h5 class="mb-1">Khisabu</h5>
                            <p class="mb-0 text-primary">Building Construction</p>
                        </div>
                    </div>
                    <p class="mb-0">Pelatihan di LPK Matahari Bulan Jepang Indonesia itu seru dan tidak membosankan. Instruktur sangat ramah dan membantu saya meningkatkan skill bahasa saya. Instruktur sangat proaktif, memberikan penjelasan yang rinci dan mudah dipahami sehingga saya lebih mudah paham</p>
                </div>
            </div>


        </div>
    </div>
</div>
<!-- Testimonials End -->

@endsection