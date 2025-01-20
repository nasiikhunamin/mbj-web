@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Struktur Organisasi</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Profile</a></li>
            <li class="breadcrumb-item active text-secondary">Struktur Organisasi</li>
        </ol>    
    </div>
</div>
<!-- Header End -->

<div class="container-fluid overflow-hidden py-5 d-flex justify-content-center align-items-center">
    <div class="container">
        <div class="row g-4 justify-content-center">
            <!-- Director -->
            <div class="col-lg-4 col-md-4 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.1s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center align-items-center">
                        <img class="img-fluid" src="{{ asset('asset/img/structure1.jpeg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Freedy Iswanto</h5>
                        <p class="text-primary">Direktur</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="row g-4 py-5 justify-content-center">
            <!-- Advisors -->
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.5s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/structure2.jpeg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Dani Lauren</h5>
                        <p class="text-primary">Manager Operasional/Pemasaran</p>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.7s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/structure3.jpeg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Jumroh Sri Ratnasari</h5>
                        <p class="text-primary">Penasihat LPK</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="row g-4 py-5 justify-content-center">
            <!-- Advisors -->
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.5s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/structure4.jpeg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Margareth Endaris Putri</h5>
                        <p class="text-primary">Sensei</p>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 wow fadeInUp d-flex justify-content-center" data-wow-delay="0.7s">
                <div class="team-item position-relative rounded overflow-hidden">
                    <div class="overflow-hidden d-flex justify-content-center">
                        <img class="img-fluid" src="{{ asset('asset/img/structure5.jpeg') }}" alt="">
                    </div>
                    <div class="team-text bg-light text-center p-4">
                        <h5>Irna Agustin</h5>
                        <p class="text-primary">Staff Administrasi/HRD</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

@endsection

