import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:permission_handler/permission_handler.dart';
import '../services/api_service.dart';

class AttendancePage extends StatefulWidget {
  @override
  _AttendancePageState createState() => _AttendancePageState();
}

class _AttendancePageState extends State<AttendancePage> {
  Map<String, dynamic>? _homeData;
  bool _isLoading = false;
  Position? _currentPosition;

  @override
  void initState() {
    super.initState();
    _loadHomeData();
    _getCurrentLocation();
  }

  Future<void> _getCurrentLocation() async {
    if (await Permission.location.request().isGranted) {
      try {
        _currentPosition = await Geolocator.getCurrentPosition();
      } catch (e) {
        print('Error getting location: $e');
      }
    }
  }

  Future<void> _loadHomeData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final result = await ApiService.getHomeData();
      if (result['status'] == 'success') {
        setState(() {
          _homeData = result;
        });
      }
    } catch (e) {
      _showError('Failed to load data');
    }

    setState(() {
      _isLoading = false;
    });
  }

  Future<void> _clockIn() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final result = await ApiService.clockIn(
        _currentPosition?.latitude,
        _currentPosition?.longitude,
      );

      if (result['status'] == 'success') {
        _showSuccess(result['message']);
        _loadHomeData();
      } else {
        _showError(result['message']);
      }
    } catch (e) {
      _showError('Clock in failed');
    }

    setState(() {
      _isLoading = false;
    });
  }

  Future<void> _clockOut() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final result = await ApiService.clockOut(
        _currentPosition?.latitude,
        _currentPosition?.longitude,
      );

      if (result['status'] == 'success') {
        _showSuccess(result['message']);
        _loadHomeData();
      } else {
        _showError(result['message']);
      }
    } catch (e) {
      _showError('Clock out failed');
    }

    setState(() {
      _isLoading = false;
    });
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.green),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading && _homeData == null) {
      return Center(child: CircularProgressIndicator());
    }

    return RefreshIndicator(
      onRefresh: _loadHomeData,
      child: SingleChildScrollView(
        physics: AlwaysScrollableScrollPhysics(),
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Summary Card
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Container(
                width: double.infinity,
                padding: EdgeInsets.all(20),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  gradient: LinearGradient(
                    colors: [Color(0xFF667eea), Color(0xFF764ba2)],
                  ),
                ),
                child: Column(
                  children: [
                    Text(
                      'This Month',
                      style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        Column(
                          children: [
                            Text(
                              '${_homeData?['total_days'] ?? 0}',
                              style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                            ),
                            Text('Days', style: TextStyle(color: Colors.white70)),
                          ],
                        ),
                        Column(
                          children: [
                            Text(
                              '${_homeData?['total_hours'] ?? 0}',
                              style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                            ),
                            Text('Hours', style: TextStyle(color: Colors.white70)),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            SizedBox(height: 20),

            // Clock In/Out Buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isLoading ? null : _clockIn,
                    icon: Icon(Icons.login, color: Colors.white),
                    label: Text('Clock In', style: TextStyle(color: Colors.white)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      padding: EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isLoading ? null : _clockOut,
                    icon: Icon(Icons.logout, color: Colors.white),
                    label: Text('Clock Out', style: TextStyle(color: Colors.white)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      padding: EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
              ],
            ),

            SizedBox(height: 20),

            // Attendance History
            Text(
              'Recent Attendance',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 10),

            if (_homeData?['attendances'] != null)
              ListView.builder(
                shrinkWrap: true,
                physics: NeverScrollableScrollPhysics(),
                itemCount: (_homeData!['attendances'] as List).length,
                itemBuilder: (context, index) {
                  final attendance = _homeData!['attendances'][index];
                  return Card(
                    margin: EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: attendance['flag'] == 2 ? Colors.green : Colors.orange,
                        child: Icon(
                          attendance['flag'] == 2 ? Icons.check : Icons.access_time,
                          color: Colors.white,
                        ),
                      ),
                      title: Text(attendance['date']),
                      subtitle: Text(
                        'In: ${attendance['clock_in'] ?? 'Not clocked'} | Out: ${attendance['clock_out'] ?? 'Not clocked'}',
                      ),
                      trailing: Text(
                        '${attendance['total_hours'] ?? 0}h',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }
}