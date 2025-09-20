import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ProjectsPage extends StatefulWidget {
  @override
  _ProjectsPageState createState() => _ProjectsPageState();
}

class _ProjectsPageState extends State<ProjectsPage> {
  List<dynamic> _projects = [];
  Map<String, dynamic>? _selectedProjectData;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadProjects();
  }

  Future<void> _loadProjects() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final result = await ApiService.getProjects();
      if (result['status'] == 'success') {
        setState(() {
          _projects = result['projects'];
        });
      }
    } catch (e) {
      _showError('Failed to load projects');
    }

    setState(() {
      _isLoading = false;
    });
  }

  Future<void> _loadProjectMaterials(int projectId) async {
    setState(() {
      _isLoading = true;
    });

    try {
      final result = await ApiService.getProjectMaterials(projectId);
      print('Project Materials API Response: $result'); // Debug line

      if (result['status'] == 'success') {
        setState(() {
          _selectedProjectData = result['aluminum_data'];
        });
        print('Aluminum data: $_selectedProjectData'); // Debug line
      } else {
        print('Materials API Error: ${result['message']}'); // Debug line
        _showError('Failed to load project materials');
      }
    } catch (e) {
      print('Materials Exception: $e'); // Debug line
      _showError('Failed to load project materials: $e');
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

  @override
  Widget build(BuildContext context) {
    if (_isLoading && _projects.isEmpty) {
      return Center(child: CircularProgressIndicator());
    }

    return RefreshIndicator(
      onRefresh: _loadProjects,
      child: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Your Projects',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),

            if (_projects.isEmpty)
              Center(
                child: Column(
                  children: [
                    Icon(Icons.work_off, size: 64, color: Colors.grey),
                    SizedBox(height: 16),
                    Text(
                      'No projects assigned',
                      style: TextStyle(fontSize: 18, color: Colors.grey),
                    ),
                  ],
                ),
              )
            else
              ListView.builder(
                shrinkWrap: true,
                physics: NeverScrollableScrollPhysics(),
                itemCount: _projects.length,
                itemBuilder: (context, index) {
                  final project = _projects[index];
                  return Card(
                    margin: EdgeInsets.only(bottom: 12),
                    elevation: 2,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: Color(0xFF667eea),
                        child: Icon(Icons.work, color: Colors.white),
                      ),
                      title: Text(
                        'Project ${project['project_number']}',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      subtitle: Text(project['address'] ?? 'No address'),
                      trailing: Icon(Icons.arrow_forward_ios),
                      onTap: () => _loadProjectMaterials(project['id']),
                    ),
                  );
                },
              ),

            // Materials section - this was missing before
            if (_selectedProjectData != null) ...[
              SizedBox(height: 20),
              Text(
                'Materials',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 16),

              // Frame Materials
              Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Frame Materials',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 10),
                      if (_selectedProjectData!['frame_totals'] != null)
                        Column(
                          children: [
                            _buildMaterialRow('Top Frame', '${_selectedProjectData!['frame_totals']['top']} cm'),
                            _buildMaterialRow('Bottom Frame', '${_selectedProjectData!['frame_totals']['bottom']} cm'),
                            _buildMaterialRow('Side Frame', '${_selectedProjectData!['frame_totals']['side']} cm'),
                          ],
                        ),
                      SizedBox(height: 10),
                      Text(
                        'Bars Needed:',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      if (_selectedProjectData!['frame_bars'] != null)
                        Column(
                          children: [
                            _buildMaterialRow('Top', '${_selectedProjectData!['frame_bars']['top']} bars'),
                            _buildMaterialRow('Bottom', '${_selectedProjectData!['frame_bars']['bottom']} bars'),
                            _buildMaterialRow('Side', '${_selectedProjectData!['frame_bars']['side']} bars'),
                          ],
                        ),
                    ],
                  ),
                ),
              ),

              SizedBox(height: 12),

              // Sash Materials
              Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Sash Materials',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 10),
                      if (_selectedProjectData!['sash_totals'] != null)
                        Column(
                          children: [
                            _buildMaterialRow('Top/Bottom', '${_selectedProjectData!['sash_totals']['top_bottom']} cm'),
                            _buildMaterialRow('Handle Side', '${_selectedProjectData!['sash_totals']['handle_side']} cm'),
                            _buildMaterialRow('Side', '${_selectedProjectData!['sash_totals']['side']} cm'),
                          ],
                        ),
                      SizedBox(height: 10),
                      Text(
                        'Bars Needed:',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      if (_selectedProjectData!['sash_bars'] != null)
                        Column(
                          children: [
                            _buildMaterialRow('Top/Bottom', '${_selectedProjectData!['sash_bars']['top_bottom']} bars'),
                            _buildMaterialRow('Handle Side', '${_selectedProjectData!['sash_bars']['handle_side']} bars'),
                            _buildMaterialRow('Side', '${_selectedProjectData!['sash_bars']['side']} bars'),
                          ],
                        ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildMaterialRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}