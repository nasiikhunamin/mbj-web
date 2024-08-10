@extends('layouts.master')
@section('content')
    <!-- Carousel Start -->
    <div class="carousel-header">
        <div id="carouselId" class="carousel slide" data-bs-ride="carousel">
            <ol class="carousel-indicators">
                <li data-bs-target="#carouselId" data-bs-slide-to="0" class="active"></li>
                <li data-bs-target="#carouselId" data-bs-slide-to="1"></li>
            </ol>
            <div class="carousel-inner" role="listbox">
                <div class="carousel-item active">
                    <img src="{{ asset('asset/img/carousel-1.jpg') }}" class="img-fluid" alt="Image">
                    <div class="carousel-caption">
                        <div class="text-center p-4" style="max-width: 900px;">
                            <h4 class="text-white text-uppercase fw-bold mb-3 mb-md-4 wow fadeInUp" data-wow-delay="0.1s">Kendala Biaya?</h4>
                            <h1 class="display-1 text-capitalize text-white mb-3 mb-md-4 wow fadeInUp" data-wow-delay="0.3s">Ikuti Kelas, Bayar Setelah Kerja di Jepang!</h1>
                            <p class="text-white mb-4 mb-md-5 fs-5 wow fadeInUp" data-wow-delay="0.5s">
                                Wujudkan impian belajar tanpa pusing biaya. Belajar di Bootcamp MJB Indonesia bisa bayar setelah lulus hingga dapat kerja!* 
                            </p>
                            <a class="btn btn-primary border-secondary rounded-pill text-white py-3 px-5 wow fadeInUp" data-wow-delay="0.7s" href="#">Daftar Sekarang!</a>
                        </div>
                    </div>
                </div>
                <div class="carousel-item">
                    <img src="{{ asset('asset/img/carousel-1.jpg') }}" class="img-fluid" alt="Image">
                    <div class="carousel-caption">
                        <div class="text-center p-4" style="max-width: 900px;">
                            <h1 class="display-1 text-capitalize text-white mb-3 mb-md-4 wow fadeInUp" data-wow-delay="0.3s">Raih karir dan kerja impian di jepang!</h1>
                            <p class="text-white mb-4 mb-md-5 fs-5 wow fadeInUp" data-wow-delay="0.5s">
                                MJB Indonesia telah menyalurkan lebih dari 30.000 talenta berkualitas untuk bekerja di Jepang.
                            </p>
                            <a class="btn btn-primary border-secondary rounded-pill text-white py-3 px-5 wow fadeInUp" data-wow-delay="0.7s" href="#">Daftar Sekarang!</a>
                        </div>
                    </div>
                </div>
            </div>
            <button class="carousel-control-prev" type="button" data-bs-target="#carouselId" data-bs-slide="prev">
                <span class="carousel-control-prev-icon bg-secondary wow fadeInLeft" data-wow-delay="0.2s" aria-hidden="false"></span>
                <span class="visually-hidden-focusable">Previous</span>
            </button>
            <button class="carousel-control-next" type="button" data-bs-target="#carouselId" data-bs-slide="next">
                <span class="carousel-control-next-icon bg-secondary wow fadeInRight" data-wow-delay="0.2s" aria-hidden="false"></span>
                <span class="visually-hidden-focusable">Next</span>
            </button>
        </div>
    </div>
    <!-- Carousel End -->


    <!-- Modal Search Start -->
    <div class="modal fade" id="searchModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-fullscreen">
            <div class="modal-content rounded-0">
                <div class="modal-header">
                    <h4 class="modal-title text-secondary mb-0" id="exampleModalLabel">Search by keyword</h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body d-flex align-items-center">
                    <div class="input-group w-75 mx-auto d-flex">
                        <input type="search" class="form-control p-3" placeholder="keywords" aria-describedby="search-icon-1">
                        <span id="search-icon-1" class="input-group-text p-3"><i class="fa fa-search"></i></span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- Modal Search End -->



    <!-- About Start -->
    <div class="container-fluid py-5">
        <div class="container py-5">
            <div class="row g-5">
                <div class="col-xl-5 wow fadeInLeft" data-wow-delay="0.1s">
                    <div class="bg-light rounded">
                        <img src="{{ asset('asset/img/about-2.png') }}" class="img-fluid w-100" style="margin-bottom: -7px;" alt="Image">
                        <img src="{{ asset('asset/img/about-3.jpg') }}" class="img-fluid w-100 border-bottom border-5 border-primary" style="border-top-right-radius: 300px; border-top-left-radius: 300px;" alt="Image">
                    </div>
                </div>
                <div class="col-xl-7 wow fadeInRight" data-wow-delay="0.3s">
                    <h5 class="sub-title pe-3">Tentang Perusahaan</h5>
                    <h1 class="display-5 mb-4">Kami adalah LPK Jepang Terpercaya.</h1>
                    <p class="mb-4">Lorem ipsum dolor sit amet consectetur adipisicing elit. Sunt architecto consectetur iusto perferendis blanditiis assumenda dignissimos, commodi fuga culpa earum explicabo libero sint est mollitia saepe! Sequi asperiores rerum nemo!</p>
                    <div class="row gy-4 align-items-center">
                        <div class="col-12 col-sm-6 d-flex align-items-center">
                            <i class="fas fa-map-marked-alt fa-3x text-secondary"></i>
                            <h5 class="ms-4">Jaminan Kerja di Jepang</h5>
                        </div>
                        <div class="col-12 col-sm-6 d-flex align-items-center">
                            <i class="fas fa-passport fa-3x text-secondary"></i>
                            <h5 class="ms-4">Dokumen Kerja Lengkap</h5>
                        </div>
                        <div class="col-4 col-md-3">
                            <div class="bg-light text-center rounded p-3">
                                <div class="mb-2">
                                    <i class="fas fa-users fa-4x text-primary"></i>
                                </div>
                                <h1 class="display-5 fw-bold mb-2">34</h1>
                                <p class="text-muted mb-0">Orang Berangkat Tahun Ini</p>
                            </div>
                        </div>
                        <div class="col-8 col-md-9">
                            <div class="mb-5">
                                <p class="text-primary h6 mb-3"><i class="fa fa-check-circle text-secondary me-2"></i> 100% Dana Talangan</p>
                                <p class="text-primary h6 mb-3"><i class="fa fa-check-circle text-secondary me-2"></i> Pelaksanaan Layanan Cepat dan Tepat</p>
                                <p class="text-primary h6 mb-3"><i class="fa fa-check-circle text-secondary me-2"></i> Dibimbing Oleh Ahlinya</p>
                            </div>
                            <div class="d-flex flex-wrap">
                                <div id="phone-tada" class="d-flex align-items-center justify-content-center me-4">
                                    <a href="" class="position-relative wow tada" data-wow-delay=".9s">
                                        <i class="fa fa-phone-alt text-primary fa-3x"></i>
                                        <div class="position-absolute" style="top: 0; left: 25px;">
                                            <span><i class="fa fa-comment-dots text-secondary"></i></span>
                                        </div>
                                    </a>
                                </div>
                                <div class="d-flex flex-column justify-content-center">
                                    <span class="text-primary">Ingin Berdiskusi Lebih Lanjut?</span>
                                    <span class="text-secondary fw-bold fs-5" style="letter-spacing: 2px;">Admin: +628123456789</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- About End -->

    <!-- Features Start -->
    <div class="container-fluid features overflow-hidden py-5">
        <div class="container">
            <div class="section-title text-center mb-5 wow fadeInUp" data-wow-delay="0.1s">
                <div class="sub-style">
                    <h5 class="sub-title text-primary px-3">Mengapa Harus Kami?</h5>
                </div>
                <h1 class="display-5 mb-4">MBJ Indonesia Menjadi Lembaga Pelatihan dan Keterampilan Kerja Terbaik </h1>
                <p class="mb-0">MBJ Indonesia sudah teruji menghasilkan para lulusan yang kompeten di industri melalui program bootcamp!</p>
            </div>
            <div class="row g-4 justify-content-center text-center">
                <div class="col-md-6 col-lg-6 col-xl-3 wow fadeInUp" data-wow-delay="0.1s">
                    <div class="feature-item text-center p-4">
                        <div class="feature-icon p-3 mb-4">
                            <i class="fas fa-dollar-sign fa-4x text-primary"></i>
                        </div>
                        <div class="feature-content d-flex flex-column">
                            <h5 class="mb-3">Dana Talangan</h5>
                            <p class="mb-3">Dolor, sit amet consectetur adipisicing elit. Soluta inventore cum accusamus,</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 col-lg-6 col-xl-3 wow fadeInUp" data-wow-delay="0.3s">
                    <div class="feature-item text-center p-4">
                        <div class="feature-icon p-3 mb-4">
                            <i class="fas fa-user-clock fa-4x text-primary"></i>
                        </div>
                        <div class="feature-content d-flex flex-column">
                            <h5 class="mb-3">Belajar Intensif</h5>
                            <p class="mb-3">Dolor, sit amet consectetur adipisicing elit. Soluta inventore cum accusamus,</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 col-lg-6 col-xl-3 wow fadeInUp" data-wow-delay="0.5s">
                    <div class="feature-item text-center p-4">
                        <div class="feature-icon p-3 mb-4">
                            <i class="fas fa-atlas fa-4x text-primary"></i>
                        </div>
                        <div class="feature-content d-flex flex-column">
                            <h5 class="mb-3">Silabus Sesuai</h5>
                            <p class="mb-3">Dolor, sit amet consectetur adipisicing elit. Soluta inventore cum accusamus,</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 col-lg-6 col-xl-3 wow fadeInUp" data-wow-delay="0.7s">
                    <div class="feature-item text-center p-4">
                        <div class="feature-icon p-3 mb-4">
                            <i class="fas fa-users fa-4x text-primary"></i>
                        </div>
                        <div class="feature-content d-flex flex-column">
                            <h5 class="mb-3">Lulusan Terbanyak</h5>
                            <p class="mb-3">Dolor, sit amet consectetur adipisicing elit. Soluta inventore cum accusamus,</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- Features End -->

    <!-- Testimonial Start -->
    <div class="container-fluid testimonial overflow-hidden py-5">
        <div class="container py-5">
            <div class="section-title text-center mb-5 wow fadeInUp" data-wow-delay="0.1s">
                <div class="sub-style">
                    <h5 class="sub-title text-primary px-3">Apa Kata Mereka</h5>
                </div>
                <h1 class="display-5 mb-4">Apa Yang Alumni Kita Katakan</h1>
                <p class="mb-0">Lorem ipsum dolor sit amet consectetur adipisicing elit. Quaerat deleniti amet at atque sequi quibusdam cumque itaque repudiandae temporibus, eius nam mollitia voluptas maxime veniam necessitatibus saepe in ab? Repellat!</p>
            </div>
            <div class="owl-carousel testimonial-carousel wow zoomInDown" data-wow-delay="0.2s">
                <div class="testimonial-item">
                    <div class="testimonial-content p-4 mb-5">
                        <p class="fs-5 mb-0">Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitati eiusmod tempor incididunt.
                        </p>
                        <div class="d-flex justify-content-end">
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                        </div>
                    </div>
                    <div class="d-flex">
                        <div class="rounded-circle me-4" style="width: 100px; height: 100px;">
                            <img class="img-fluid rounded-circle" src="{{ asset('asset/img/testimonial-1.jpg') }}" alt="img">
                        </div>
                        <div class="my-auto">
                            <h5>Person Name</h5>
                            <p class="mb-0">Profession</p>
                        </div>
                    </div>
                </div>
                <div class="testimonial-item">
                    <div class="testimonial-content p-4 mb-5">
                        <p class="fs-5 mb-0">Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitati eiusmod tempor incididunt.
                        </p>
                        <div class="d-flex justify-content-end">
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                        </div>
                    </div>
                    <div class="d-flex">
                        <div class="rounded-circle me-4" style="width: 100px; height: 100px;">
                            <img class="img-fluid rounded-circle" src="{{ asset('asset/img/testimonial-2.jpg') }}" alt="img">
                        </div>
                        <div class="my-auto">
                            <h5>Person Name</h5>
                            <p class="mb-0">Profession</p>
                        </div>
                    </div>
                </div>
                <div class="testimonial-item">
                    <div class="testimonial-content p-4 mb-5">
                        <p class="fs-5 mb-0">Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitati eiusmod tempor incididunt.
                        </p>
                        <div class="d-flex justify-content-end">
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                            <i class="fas fa-star text-secondary"></i>
                        </div>
                    </div>
                    <div class="d-flex">
                        <div class="rounded-circle me-4" style="width: 100px; height: 100px;">
                            <img class="img-fluid rounded-circle" src="{{ asset('asset/img/testimonial-3.jpg') }}" alt="img">
                        </div>
                        <div class="my-auto">
                            <h5>Person Name</h5>
                            <p class="mb-0">Profession</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- Testimonial End -->

@endsection