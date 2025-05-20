import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { Zap, MapPin, Briefcase, Calendar, DollarSign, ThumbsUp, AlertCircle } from 'lucide-react';

interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  description: string;
  requirements: string[];
  salary_range?: string;
  posted_date: string;
  is_remote: boolean;
  job_type: string;
}

interface JobRecommendation {
  job_id: number;
  match_score: number;
  match_reasons: string[];
}

const RecommendationsPage: React.FC = () => {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState<JobRecommendation[]>([]);
  const [jobs, setJobs] = useState<Record<number, Job>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        // Fetch recommendations
        const recommendationsResponse = await axios.get('http://localhost:8000/recommendations/');
        setRecommendations(recommendationsResponse.data);
        
        // Fetch all jobs to get details for each recommendation
        const jobsResponse = await axios.get('http://localhost:8000/jobs/');
        const jobsMap: Record<number, Job> = {};
        jobsResponse.data.forEach((job: Job) => {
          jobsMap[job.id] = job;
        });
        setJobs(jobsMap);
      } catch (err) {
        console.error('Error fetching recommendations:', err);
        setError('Failed to load job recommendations. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchRecommendations();
  }, []);
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  };
  
  const formatMatchScore = (score: number) => {
    return Math.round(score * 100);
  };
  
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-8">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">AI Job Recommendations</h1>
          <p className="mt-2 text-sm text-gray-600">
            Personalized job matches based on your skills and preferences
          </p>
        </div>
        
        {recommendations.length === 0 ? (
          <div className="bg-white p-6 rounded-lg shadow-sm text-center">
            <Zap className="h-12 w-12 text-blue-500 mx-auto mb-4" />
            <h2 className="text-xl font-medium text-gray-900 mb-2">No recommendations yet</h2>
            <p className="text-gray-500 mb-6">
              Update your profile with more skills and experience to get personalized job recommendations.
            </p>
            <Link
              to="/profile"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Update Profile
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {recommendations.map((recommendation) => {
              const job = jobs[recommendation.job_id];
              if (!job) return null;
              
              return (
                <div key={recommendation.job_id} className="bg-white shadow-sm rounded-lg overflow-hidden hover:shadow-md transition-shadow duration-300">
                  <div className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900">
                          <Link to={`/jobs/${job.id}`} className="hover:text-blue-600">
                            {job.title}
                          </Link>
                        </h2>
                        <div className="mt-1 flex items-center text-sm text-gray-500">
                          <Briefcase className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                          <span>{job.company}</span>
                        </div>
                      </div>
                      <div className="mt-2 md:mt-0">
                        <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                          <ThumbsUp className="h-4 w-4 mr-1" />
                          {formatMatchScore(recommendation.match_score)}% Match
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-4">
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {job.description}
                      </p>
                    </div>
                    
                    <div className="mt-4 bg-blue-50 p-3 rounded-md">
                      <h3 className="text-sm font-medium text-blue-800 mb-2">Why this job matches your profile:</h3>
                      <ul className="space-y-1">
                        {recommendation.match_reasons.map((reason, index) => (
                          <li key={index} className="text-sm text-blue-700 flex items-start">
                            <span className="inline-block h-4 w-4 mr-1.5 mt-0.5 text-blue-500">•</span>
                            {reason}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="mt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex items-center text-sm text-gray-500">
                        <div className="flex items-center mr-6">
                          <MapPin className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                          <span>{job.is_remote ? 'Remote' : job.location}</span>
                        </div>
                        {job.salary_range && (
                          <div className="flex items-center mr-6">
                            <DollarSign className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                            <span>{job.salary_range}</span>
                          </div>
                        )}
                        <div className="flex items-center">
                          <Calendar className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                          <span>Posted {formatDate(job.posted_date)}</span>
                        </div>
                      </div>
                      
                      <div className="mt-4 sm:mt-0">
                        <Link
                          to={`/jobs/${job.id}`}
                          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          View Details
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default RecommendationsPage;