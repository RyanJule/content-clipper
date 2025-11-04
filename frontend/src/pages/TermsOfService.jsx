import { ArrowLeft, FileText } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link
            to="/"
            className="inline-flex items-center text-primary-600 hover:text-primary-700 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Link>
          <div className="flex items-center space-x-3">
            <FileText className="w-8 h-8 text-primary-600" />
            <h1 className="text-3xl font-bold text-gray-900">Terms of Service</h1>
          </div>
          <p className="text-gray-600 mt-2">Last updated: November 3, 2025</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="prose prose-gray max-w-none">
            
            {/* Introduction */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Agreement to Terms</h2>
              <p className="text-gray-700 mb-4">
                By accessing and using Content Clipper ("the Service"), you accept and agree to be bound by the terms and provision of this agreement.
              </p>
              <p className="text-gray-700">
                If you do not agree to these Terms of Service, please do not use the Service.
              </p>
            </section>

            {/* Use of Service */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Use of Service</h2>
              <p className="text-gray-700 mb-4">
                Content Clipper provides tools for video clipping, content management, and social media scheduling. You agree to use the Service only for lawful purposes and in accordance with these Terms.
              </p>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">You agree NOT to:</h3>
              <ul className="list-disc pl-6 text-gray-700 space-y-2">
                <li>Use the Service for any illegal or unauthorized purpose</li>
                <li>Violate any laws in your jurisdiction</li>
                <li>Infringe upon or violate intellectual property rights of others</li>
                <li>Upload malicious code, viruses, or any harmful content</li>
                <li>Attempt to gain unauthorized access to the Service</li>
                <li>Use the Service to spam or distribute unsolicited content</li>
                <li>Impersonate any person or entity</li>
              </ul>
            </section>

            {/* User Accounts */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. User Accounts</h2>
              <p className="text-gray-700 mb-4">
                You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account.
              </p>
              <p className="text-gray-700 mb-4">
                You must notify us immediately of any unauthorized access to or use of your account.
              </p>
              <p className="text-gray-700">
                We reserve the right to suspend or terminate accounts that violate these Terms.
              </p>
            </section>

            {/* Content and Intellectual Property */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Content and Intellectual Property</h2>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Your Content</h3>
              <p className="text-gray-700 mb-4">
                You retain all rights to the content you upload to Content Clipper. By uploading content, you grant us a limited license to process, store, and display your content solely for the purpose of providing the Service.
              </p>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Third-Party Content</h3>
              <p className="text-gray-700 mb-4">
                You are responsible for ensuring you have the necessary rights and permissions to use any third-party content in your clips and posts.
              </p>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Our Intellectual Property</h3>
              <p className="text-gray-700">
                The Service and its original content, features, and functionality are owned by Content Clipper and are protected by international copyright, trademark, and other intellectual property laws.
              </p>
            </section>

            {/* Social Media Integration */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Social Media Integration</h2>
              <p className="text-gray-700 mb-4">
                When you connect your social media accounts to Content Clipper, you authorize us to access and post content on your behalf according to your instructions.
              </p>
              <p className="text-gray-700 mb-4">
                You are responsible for complying with the terms of service of each social media platform you connect.
              </p>
              <p className="text-gray-700">
                We are not responsible for any actions taken by third-party platforms or changes to their APIs or policies.
              </p>
            </section>

            {/* Privacy and Data */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Privacy and Data</h2>
              <p className="text-gray-700 mb-4">
                Your use of the Service is also governed by our Privacy Policy. We collect and use your data as described in our Privacy Policy.
              </p>
              <p className="text-gray-700">
                We implement reasonable security measures to protect your data, but cannot guarantee absolute security.
              </p>
            </section>

            {/* Payment and Subscription */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Payment and Subscription</h2>
              <p className="text-gray-700 mb-4">
                If you subscribe to a paid plan, you agree to pay all fees associated with your subscription.
              </p>
              <p className="text-gray-700 mb-4">
                Subscriptions automatically renew unless cancelled before the renewal date.
              </p>
              <p className="text-gray-700">
                We reserve the right to change our pricing with 30 days notice to existing subscribers.
              </p>
            </section>

            {/* Limitation of Liability */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Limitation of Liability</h2>
              <p className="text-gray-700 mb-4">
                THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED.
              </p>
              <p className="text-gray-700 mb-4">
                Content Clipper shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use or inability to use the Service.
              </p>
              <p className="text-gray-700">
                Our total liability shall not exceed the amount you paid us in the past 12 months.
              </p>
            </section>

            {/* Service Modifications */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Service Modifications and Termination</h2>
              <p className="text-gray-700 mb-4">
                We reserve the right to modify or discontinue the Service at any time without notice.
              </p>
              <p className="text-gray-700">
                We may terminate or suspend your account immediately, without prior notice, for conduct that we believe violates these Terms.
              </p>
            </section>

            {/* Indemnification */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Indemnification</h2>
              <p className="text-gray-700">
                You agree to indemnify and hold harmless Content Clipper and its affiliates from any claims, damages, losses, or expenses arising from your use of the Service or violation of these Terms.
              </p>
            </section>

            {/* Dispute Resolution */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Dispute Resolution</h2>
              <p className="text-gray-700 mb-4">
                Any disputes arising from these Terms shall be resolved through binding arbitration in accordance with the rules of the American Arbitration Association.
              </p>
              <p className="text-gray-700">
                You waive your right to participate in class action lawsuits or class-wide arbitration.
              </p>
            </section>

            {/* Changes to Terms */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Changes to Terms</h2>
              <p className="text-gray-700 mb-4">
                We reserve the right to modify these Terms at any time. We will notify users of any material changes.
              </p>
              <p className="text-gray-700">
                Your continued use of the Service after changes constitutes acceptance of the new Terms.
              </p>
            </section>

            {/* Governing Law */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">13. Governing Law</h2>
              <p className="text-gray-700">
                These Terms shall be governed by and construed in accordance with the laws of the United States, without regard to its conflict of law provisions.
              </p>
            </section>

            {/* Contact */}
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">14. Contact Information</h2>
              <p className="text-gray-700 mb-2">
                If you have any questions about these Terms, please contact us at:
              </p>
              <div className="text-gray-700">
                <p>Email: support@contentclipper.com</p>
                <p>Website: https://contentclipper.com</p>
              </div>
            </section>

            {/* Acceptance */}
            <section className="bg-primary-50 border border-primary-200 rounded-lg p-6 mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Acknowledgment</h3>
              <p className="text-gray-700">
                BY USING CONTENT CLIPPER, YOU ACKNOWLEDGE THAT YOU HAVE READ THESE TERMS OF SERVICE AND AGREE TO BE BOUND BY THEM.
              </p>
            </section>

          </div>
        </div>
      </div>
    </div>
  )
}