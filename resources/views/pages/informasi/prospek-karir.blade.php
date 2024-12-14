@extends('layouts.master')
@section('content')

<!-- Header Start -->
<div class="container-fluid bg-breadcrumb">
    <div class="container text-center py-5" style="max-width: 900px;">
        <h3 class="text-white display-3 mb-4 wow fadeInDown" data-wow-delay="0.1s">Prospek Karir</h1>
        <ol class="breadcrumb justify-content-center text-white mb-0 wow fadeInDown" data-wow-delay="0.3s">
            <li class="breadcrumb-item"><a href="index.html" class="text-white">Home</a></li>
            <li class="breadcrumb-item"><a href="#" class="text-white">Informasi</a></li>
            <li class="breadcrumb-item active text-secondary">Prospek Karir</li>
        </ol>    
    </div>
</div>

    <style>
        .career-prospects {
            background-color: #f4f6f9;
            padding: 60px 0;
        }
        .job-card {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .job-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.15);
        }
        .job-card-img {
            height: 250px;
            object-fit: cover;
            width: 100%;
        }
        .job-card-body {
            padding: 20px;
            text-align: center;
        }
        .job-card-title {
            color: #2c3e50;
            font-weight: 600;
            margin-bottom: 15px;
        }
        .job-card-description {
            color: #7f8c8d;
            margin-bottom: 15px;
        }
    </style>

    <div class="career-prospects">
        <div class="container">
            <div class="row">
                <div class="col-12 text-center mb-5">
                    <h1 class="display-4">Specified Skilled Worker (SSW)</h1>
                    <p class="lead text-muted">Temukan Jalan Menarik Menuju Masa Depan Kamu</p>
                </div>
            </div>
            
            <div class="row">
                @php
                    $jobOpportunities = [
                        [
                            'title' => 'Agriculture Job',
                            'image' => asset('asset/img/agriculture.jpeg'),
                            'description' => 'Bertani, berkebun, dan pekerjaan lain yang terkait dengan produksi hasil tani',
                        ],
                        [
                            'title' => 'Caregiver Job',
                            'image' => asset('asset/img/caregiver.jpeg'),
                            'description' => 'Merawat dan membantu aktivitas harian para lansia di fasilitas kesehatan atau rumah',
                        ],
                        [
                            'title' => 'Cleaning Service Job',
                            'image' => asset('asset/img/cleaning-service.jpeg'),
                            'description' => 'Membersihkan dan merawat gedung atau fasilitas lainnya.',
                        ],
                        [
                            'title' => 'Construction Job',
                            'image' => asset('asset/img/construction.jpeg'),
                            'description' => 'Proyek pembangunan dan renovasi infrastruktur, seperti gedung dan jalan',
                        ],
                        [
                            'title' => 'Industry Job',
                            'image' => asset('asset/img/industry.jpeg'),
                            'description' => 'Memproduksi, merakit, atau memelihara peralatan mesin',
                        ],
                        [
                            'title' => 'Manufacture Job',
                            'image' => asset('asset/img/manufacture.jpeg'),
                            'description' => 'Provide exceptional service and build lasting customer relationships.',
                        ],
                        [
                            'title' => 'Nurse Job',
                            'image' => asset('asset/img/nurse.jpeg'),
                            'description' => 'Provide exceptional service and build lasting customer relationships.',
                        ],
                        [
                            'title' => 'Food Service',
                            'image' => asset('asset/img/restaurant.jpeg'),
                            'description' => 'Bekerja di restoran atau layanan makanan, termasuk memasak dan melayani pelanggan',
                        ],
                    ];
                @endphp

                @foreach($jobOpportunities as $job)
                <div class="col-md-3 col-sm-6">
                    <div class="job-card">
                        <img src="{{ $job['image'] }}" alt="{{ $job['title'] }}" class="job-card-img">
                        <div class="job-card-body">
                            <h3 class="job-card-title">{{ $job['title'] }}</h3>
                            <p class="job-card-description">{{ $job['description'] }}</p>
                        </div>
                    </div>
                </div>
                @endforeach
            </div>
        </div>
    </div>

@endsection